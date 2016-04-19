/**
  * Codigo auxiliar para problema de reversao de classificacao:
  * extrai lista de regras a partir da saida do classificador RandomForests do WEKA.
  *
  * Tiberius Bonates, Manoel Campelo, Michael Souza
  * Universidade Federal do Ceara, 2016.
 **/
#include <iostream>
#include <iomanip>
#include <fstream>
#include <string>
#include <sstream>
#include <list>
#include <map>
#include <set>
#include <vector>

using namespace std;

enum TipoRel {
	menor, maior, igual
};

struct Teste {
	string variavel, valor;
	TipoRel relacao;
};

vector<string> split(string original, char delimitador) {
	vector<string> partes;

	stringstream ss( original );
	string parte;
	while (getline(ss, parte, delimitador))
		partes.push_back( parte );

	return partes;
}

void imprimir(list<Teste> r) {
	cout << "Regra: [";
	for (Teste t : r) {
		cout << " " << t.variavel;
		if (t.relacao == igual)
			cout << "=";
		else if (t.relacao == menor)
			cout << "<";
		else
			cout << ">=";
		cout << t.valor;
	}
	cout << " ]" << endl;
}

int main() {

	ifstream arq("floresta.txt");
	if (!arq.is_open()) {
		cout << "Nao posso abrir o arquivo." << endl;
		return 1;
	}

	cout << "Lendo arquivo... ";
	string linha;
	list<Teste> regra; // Armazena testes lidos desde a raiz
	int numeroDeRegras = 0;

	list< list<Teste> > RegrasPositivas, RegrasNegativas;

	string classePositiva = ""; // Retem a etiqueta da primeira regra lida.
	                            // Etiquetas diferentes sao consideradas como 'classe negativa'.

	while (1) {

		do {
			getline(arq, linha);
		} while ((!arq.eof()) && (linha != "RandomTree"));
		if (arq.eof())
			break;
		getline(arq, linha); // ==========
		getline(arq, linha); // linha em branco

		getline(arq, linha);
		while (linha != "") {

			vector<string> partes;
			if (linha[0] != '|') { // Estamos no nivel da raiz
				regra.clear();
				partes = split(linha, ' ');
			}
			else {
				// Detectar nivel do teste na arvore e ajustar 'regra' de acordo
				int i = 0,     // 'i' vai conter a posicao onde o teste se inicia
					nivel = 0; // 'nivel' e' a profundidade do teste dentro da arvore
				while ((linha[i] == ' ') || (linha[i] == '|')) {
					if (linha[i] == '|')
						nivel ++;
					i++;
				}
				// 'regra' e' tratada como uma pilha, com topo no final
				while (nivel < regra.size())
					regra.pop_back();

				string resto;
				for (int k=i; k<linha.length(); k++)
					resto.push_back( linha[k] );
				partes = split(resto, ' ');
			}

			// Montar novo teste e inseri-lo na regra em construcao
			Teste novo = {partes[0], partes[2], igual};
			if (partes[1] == "<=") {
				novo.relacao = menor;
			}
			else if (partes[1] == ">") {
				novo.relacao = maior;
			}
			regra.push_back( novo );

			// Se regra tiver chegado ao fim
			if (partes.size() > 3) {
				++ numeroDeRegras;
				// Reter primeira etiqueta como indicativa da classe positiva
				if (numeroDeRegras == 1)
					classePositiva = partes[4];
				// Determinar classe da regra
				if (partes[4] == classePositiva)
					RegrasPositivas.push_back( regra );
				else
					RegrasNegativas.push_back( regra );
			}

			getline(arq, linha);
		}
	}

	cout << "Leitura concluida." << endl;
	arq.close();

	cout << endl << "Numero de regras lidas: " << numeroDeRegras << endl;


	// Pos-processamento
	// Identificar features e atribuir indices aas mesmas
	map<string,int> variaveis;
	int indice = 1;
	for (list<Teste> r : RegrasPositivas)
		for (Teste t : r)
			if (variaveis[t.variavel] == 0)
				variaveis[t.variavel] = indice ++;
	for (list<Teste> r : RegrasNegativas)
		for (Teste t : r)
			if (variaveis[t.variavel] == 0)
				variaveis[t.variavel] = indice ++;

	cout << "Numero de features utilizadas: " << variaveis.size() << endl;

	cout << "Etiqueta da classe positiva: " << classePositiva << "." << endl << endl;

	cout << "Mapeamento de features originais para coordenadas binarias: " << endl;
	map< string,set<string> > valores;
	for (pair<string,int> p : variaveis) {
		cout << "\tx" << p.second << "\t---\t" << p.first << endl;
		valores[p.first] = set<string>();
	}

	// Detectar valores utilizados nas regras
	for (list<Teste> r : RegrasPositivas)
		for (Teste t : r)
			valores[ t.variavel ].insert( t.valor );
	for (list<Teste> r : RegrasNegativas)
		for (Teste t : r)
			valores[ t.variavel ].insert( t.valor );

	// Decidir se dados sao binarios (ou podem ser considerados assim)
	bool dadosBinarios = true;
	for (pair< string,set<string> > p : valores) {
		if (p.second.size() > 2) {
			dadosBinarios = false;
			cout << "Variavel x" << variaveis[p.first] << " nao e' binaria." << endl;
			for (string v : p.second)
				cout << "\t" << v << endl;
		}
	}

	if (dadosBinarios == false)
		return 1;

	// Exportar dados em formato binario
	cout << endl << "Regras em formato binario:" << endl;

	// Percorrer ambos os conjuntos de regras
	list< list<Teste> > *Regras;
	for (int k=0; k<2; k++) {
		if (k == 0)
			Regras = &RegrasPositivas;
		else
			Regras = &RegrasNegativas;

		for (list<Teste> r : *Regras) {
			int *vetor = new int[variaveis.size()];
			for (int i=0; i<variaveis.size(); i++)
				vetor[i] = 0;

			for (Teste t : r) {
				if (t.relacao == menor) {
					vetor[variaveis[t.variavel] - 1] = -1;
				}
				else if (t.relacao == maior) {
					vetor[variaveis[t.variavel] - 1] = +1;
				}
				else {
					if (t.valor == *valores[t.variavel].begin())
						vetor[variaveis[t.variavel] - 1] = -1;
					else
						vetor[variaveis[t.variavel] - 1] = +1;
				}
			}

			//imprimir( r );
			for (int i=0; i<variaveis.size(); i++)
				cout << setw(3) << vetor[i];

			if (k == 0)
				cout << setw(3) <<  1 << endl; // Regra positiva
			else
				cout << setw(3) << -1 << endl; // Regra negativa

			delete [] vetor;
		}
	}

	//system("pause");
	return 0;
}