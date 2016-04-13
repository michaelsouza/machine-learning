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
	for (list<Teste>::iterator t = r.begin(); t != r.end(); t++) {
		cout << " " << t->variavel;
		if (t->relacao == igual)
			cout << "=";
		else if (t->relacao == menor)
			cout << "<";
		else
			cout << ">=";
		cout << t->valor;
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
	list<Teste> regra; // Armazena testes
	int numeroDeRegras = 0;

	list< list<Teste> > Regras;

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

			if (linha[0] != '|') { // Estamos no nivel da raiz
				regra.clear();
				vector<string> partes = split(linha, ' ');
				Teste novo = {partes[0], partes[2], igual};
				if (partes[1] == "<=") {
					novo.relacao = menor;
				}
				else if (partes[1] == ">") {
					novo.relacao = maior;
				}
				regra.push_back( novo );

				if (partes.size() > 3) { // Fim de regra
					//imprimir( regra );
					Regras.push_back( regra );
					++ numeroDeRegras;
				}
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
				vector<string> partes = split(resto, ' ');
				Teste novo = {partes[0], partes[2], igual};
				if (partes[1] == "<=") {
					novo.relacao = menor;
				}
				else if (partes[1] == ">") {
					novo.relacao = maior;
				}
				regra.push_back( novo );

				if (partes.size() > 3) { // Fim de regra
					//imprimir( regra );
					Regras.push_back( regra );
					++ numeroDeRegras;
				}
			}

			getline(arq, linha);
		}
	}

	cout << "Leitura concluida." << endl;
	arq.close();

	cout << "Numero de regras lidas: " << numeroDeRegras << endl << endl;

	// Pos-processamento
	map<string,int> variaveis;
	int indice = 1;
	for (list< list<Teste> >::iterator r = Regras.begin(); r != Regras.end(); r++)
		for (list<Teste>::iterator t = r->begin(); t != r->end(); t++)
			if (variaveis[t->variavel] == 0)
				variaveis[t->variavel] = indice ++;


	cout << "Mapeamento de features originais para coordenadas binarias: " << endl;
	map< string,set<string> > valores;
	for (map<string,int>::iterator p = variaveis.begin(); p != variaveis.end(); p++) {
		cout << "\tx" << p->second << "\t---\t" << p->first << endl;
		valores[p->first] = set<string>();
	}

	// Detectar valores utilizados nas regras
	for (list< list<Teste> >::iterator r = Regras.begin(); r != Regras.end(); r++)
		for (list<Teste>::iterator t = r->begin(); t != r->end(); t++)
			valores[ t->variavel ].insert( t->valor );

	// Decidir se dados sao binarios (ou podem ser considerados assim)
	bool dadosBinarios = true;
	for (map< string,set<string> >::iterator p = valores.begin(); p != valores.end(); p++) {
		if (p->second.size() > 2) {
			dadosBinarios = false;
			cout << "Variavel x" << variaveis[p->first] << " nao e' binaria." << endl;
			for (set<string>::iterator v = p->second.begin(); v != p->second.end(); v++)
				cout << "\t" << *v << endl;
		}
	}

	if (dadosBinarios == false)
		return 1;

	// Exportar dados em formato binario
	cout << endl << "Regras em formato binario:" << endl;
	for (list< list<Teste> >::iterator r = Regras.begin(); r != Regras.end(); r++) {
		int *vetor = new int[variaveis.size()];
		for (int i=0; i<variaveis.size(); i++)
			vetor[i] = 0;

		for (list<Teste>::iterator t = r->begin(); t != r->end(); t++) {
			if (t->relacao == menor) {
				vetor[variaveis[t->variavel] - 1] = -1;
			}
			else if (t->relacao == maior) {
				vetor[variaveis[t->variavel] - 1] = +1;
			}
			else {
				if (t->valor == *valores[t->variavel].begin())
					vetor[variaveis[t->variavel] - 1] = -1;
				else
					vetor[variaveis[t->variavel] - 1] = +1;
			}
		}

		//imprimir( *r );
		for (int i=0; i<variaveis.size(); i++)
			cout << setw(3) << vetor[i];
		cout << endl;
		delete [] vetor;
	}


	getchar();
	return 0;
}