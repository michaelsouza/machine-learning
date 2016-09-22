#include <ilcplex/ilocplex.h>
#include <fstream>
#include <list>
#include <string>
#include <vector>
#include "DRule.hpp"

using namespace std;

ILOSTLBEGIN

/**  Model for Classification Reversal
  *  We follow closely the formulation described in the ISAIM'14 paper
  */
class ClassReversal {
private:
	IloEnv _env;
	IloModel *_model;
	IloNumVarArray _ZVar, _YVar;

	int _numAttributes, _numRules;
	list<DRule> _rules;
	vector<int> _observation;

public:

	ClassReversal(int numberAttributes, vector<int> obs, const list<DRule> &rules, bool continuousRelaxation=false) {
		_numAttributes = numberAttributes;
		_numRules = rules.size();
		_rules = list<DRule>( rules );
		_observation = vector<int>( obs );

		try {
			_model = new IloModel( _env );
			_ZVar = IloNumVarArray( _env );
			_YVar = IloNumVarArray( _env );

			// Create decision variables
			// --- Continuous relaxation
			if (continuousRelaxation) {
				for (int i=0; i<_numAttributes; i++)
					_ZVar.add(IloNumVar(_env, 0.0, 1.0, ILOFLOAT));
				for (int j=0; j<_numRules; j++)
					_YVar.add(IloNumVar(_env, 0.0, 1.0, ILOFLOAT));
			}
			else { // --- Integrality constraints
				for (int i=0; i<_numAttributes; i++)
					_ZVar.add(IloNumVar(_env, 0.0, 1.0, ILOINT));
				for (int j=0; j<_numRules; j++)
					_YVar.add(IloNumVar(_env, 0.0, 1.0, ILOINT));
			}
		}
		catch (IloException& e) {
			cerr << "Concert exception caught: " << e << endl;
		}
		catch (...) {
			cerr << "Unknown exception caught" << endl;
		}
	}

	~ClassReversal() {
		_env.end();
	}

	// Specify the objective function and sense of optimization
	// -- minimize number of attribute changes
	void objective() {
		IloObjective obj = IloMinimize( _env );
		for (int i=0; i<_numAttributes; i++)
			obj.setLinearCoef(_ZVar[i], 1.0);
		_model->add( obj );
	}

	// Constraint sets (4) and (5)
	void addConstraints4and5() {

		int ruleIndex = 0;
		for (DRule r : _rules) {
			IloRangeArray constraints4and5( _env );
			IloRangeArray constraint4aggreg( _env );
			int ctrIndex = 0, conflicts = 0;
			// We are using here the disaggregated version of constraint (4)
			for (int lit : r.getLiterals()) {
				int varIndex = abs( lit ) - 1;

				if (((_observation[varIndex]) && (lit > 0)) || ((!_observation[varIndex]) && (lit < 0))) {
					constraints4and5.add( IloRange(_env, -IloInfinity, 1.0) );
					constraints4and5[ctrIndex].setLinearCoef(_YVar[ruleIndex], 1.0);
					constraints4and5[ctrIndex].setLinearCoef(_ZVar[varIndex], 1.0);
				}
				else {
					constraints4and5.add( IloRange(_env, -IloInfinity, 0.0) );
					constraints4and5[ctrIndex].setLinearCoef(_YVar[ruleIndex], 1.0);
					constraints4and5[ctrIndex].setLinearCoef(_ZVar[varIndex], -1.0);

					++ conflicts;
				}
				++ ctrIndex;
			}

			// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
			// Should we ad  the aggregated form of (4)?
			// --> It does not help with the LP relaxation.
			/*float rhs = r.size() - conflicts;

			constraint4aggreg.add( IloRange(_env, -IloInfinity, rhs) );

			constraint4aggreg[0].setLinearCoef(_YVar[ruleIndex], r.size());
			for (int lit : r.getLiterals()) {
				int varIndex = abs( lit ) - 1;

				if (((_observation[varIndex]) && (lit > 0)) || ((!_observation[varIndex]) && (lit < 0))) {
					constraint4aggreg[0].setLinearCoef(_ZVar[varIndex],  1.0);
				}
				else {
					constraint4aggreg[0].setLinearCoef(_ZVar[varIndex], -1.0);
				}
			}
			_model->add( constraint4aggreg );*/
			// &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

			// Constraint (5)
			constraints4and5.add( IloRange(_env, (1-conflicts), IloInfinity) );
			constraints4and5[ctrIndex].setLinearCoef(_YVar[ruleIndex], 1.0);
			for (int lit : r.getLiterals()) {
				int varIndex = abs( lit ) - 1;

				if (((_observation[varIndex]) && (lit > 0)) || ((!_observation[varIndex]) && (lit < 0)))
					constraints4and5[ctrIndex].setLinearCoef(_ZVar[varIndex], 1.0);
				else
					constraints4and5[ctrIndex].setLinearCoef(_ZVar[varIndex], -1.0);
			}

			_model->add( constraints4and5 );

			++ ruleIndex;
		}
	}

	// Constraint (6) from the ISAIM'14 model
	void addConstraint6() {

		// ------------------------------------
		// Determine original classification
		int margin = 0, Fx;
		for (DRule r : _rules) {
			bool sat = true;
			for (int lit : r.getLiterals()) {
				int varIndex = abs( lit ) - 1;
				if (((_observation[varIndex]) && (lit < 0)) || ((!_observation[varIndex]) && (lit > 0)))
					{ sat = false; break; }
			}
			if (sat)
				margin += (r.getClass())? 1 : -1;
		}
		Fx = (margin > 0)? 1 : -1;
		//cout << "F(x) = " << Fx << " (margin = " << margin << ")" << endl;

		// ------------------------------------
		IloRangeArray constraint6( _env );
		constraint6.add( IloRange(_env, -IloInfinity, -1.0) );

		int ruleIndex = 0;
		for (DRule r : _rules) {
			if (r.getClass())
				constraint6[0].setLinearCoef(_YVar[ruleIndex], Fx);
			else
				constraint6[0].setLinearCoef(_YVar[ruleIndex], -Fx);
			++ ruleIndex;
		}
		_model->add( constraint6 );
	}

	// Constraints concerning the rule conflict graph
	void addConflictConstraints() {

		IloRangeArray conflicts( _env );
		int conflictIndex = 0;
		int ruleIndex = 0;
		int i1=0;
		for (DRule r1 : _rules) {
			int i2=0;
			for (DRule r2 : _rules) {
				if (i1 > i2) {
					bool thereIsAConflict = false;

					for (int v1 : r1.getLiterals())
						for (int v2 : r2.getLiterals())
							if (v1 == -v2) {
								thereIsAConflict = true;
								break;
							}

					if (thereIsAConflict) {
						conflicts.add( IloRange(_env, -IloInfinity, 1.0) );
						conflicts[conflictIndex].setLinearCoef(_YVar[i1], 1.0);
						conflicts[conflictIndex].setLinearCoef(_YVar[i2], 1.0);
						++ conflictIndex;
					}
				}
				++ i2;
			}
			++ i1;
		}

		_model->add( conflicts );
	}

	string solve(float &objValue, vector<float> &zvars, vector<float> &yvars) {

		try {
			IloCplex cplex( *_model );
			cplex.solve();
			//cplex.exportModel( "cr.lp" );

			string status = "optimal";
			if (cplex.getStatus() != IloAlgorithm::Status::Optimal)
				status = "bad";

			// -----------------------------------------------
			// Collect solution info
			if (status == "optimal") {
				objValue = (float) cplex.getObjValue();

				IloNumArray Zvals( _env ), Yvals( _env );
				cplex.getValues(Zvals, _ZVar);
				cplex.getValues(Yvals, _YVar);
				zvars.resize( _numAttributes );
				yvars.resize( _numRules );

				for (int i=0; i<_numAttributes; i++) zvars[i] = (float) Zvals[i];
				for (int j=0; j<_numRules; j++) yvars[j] = (float) Yvals[j];
			}
			return status;
		}
		catch (IloException& e) {
			cerr << "Concert exception caught: " << e << endl;
		}
		catch (...) {
			cerr << "Unknown exception caught" << endl;
		}
		return "error";
	}

};

void readData(string fileName, int &numberAttributes, list<DRule> &rules)
{
	ifstream input;
	input.open("rules.txt");

	if (! input.is_open()) {
		cout << endl << "Input file cannot be opened!" << endl << endl;
		return;
	}

	input >> numberAttributes;

	while ((input.is_open()) && (! input.eof())) {

		list<int> tests;
		int atest, // A single test within the rule
			cl;    // The class info of the rule
		for (int i = 1; i <= numberAttributes; i++) {
			input >> atest;
			if (input.eof())
				break;

			if (atest > 0)
				tests.push_back( i );
			else if (atest < 0)
				tests.push_back( -i );
		}
		if (input.eof())
			break;

		input >> cl;

		DRule rule(tests, (cl > 0));
		//rule.print();
		rules.push_back( rule );
	}

	input.close();
}

int main (void)
{

	// Read data
	int numberAttributes;
	list<DRule> rules;
	readData("rules.txt", numberAttributes, rules);

	vector<int> observation( numberAttributes );
	for (int i=0; i<numberAttributes; i++)
		observation[i] = false;

	float relaxObjVal, ipObjVal;
	vector<float> solZ, solY;

	/*ClassReversal lprelax(numberAttributes, observation, rules, true);
	lprelax.objective();
	lprelax.addConstraints4and5();
	lprelax.addConstraint6();
	lprelax.solve(relaxObjVal, solZ, solY);

	cout << endl << endl << "*************************************************************";
	cout << endl << endl;*/


	ClassReversal ip(numberAttributes, observation, rules, false);
	ip.objective();
	ip.addConstraints4and5();
	ip.addConstraint6();
	ip.solve(ipObjVal, solZ, solY);

	cout << endl << "IP model optimum value: " << ipObjVal << endl;
	//--------------------------------------------------

	system("pause");
	return 0;
}
