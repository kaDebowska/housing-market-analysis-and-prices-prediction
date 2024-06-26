import click
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from lightgbm import LGBMRegressor
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from skopt import BayesSearchCV
from skopt.space import Real, Categorical, Integer
from sklearn.model_selection import train_test_split


MODELS_DICT = {
    'Lasso': Lasso(),
    'DT': DecisionTreeRegressor(),
    'RF': RandomForestRegressor(),
    'LGB': LGBMRegressor(),
    'GBM': GradientBoostingRegressor(),
    'XGB': XGBRegressor()
}

MODELS_PARAMS = {
    'Lasso': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__alpha': Real(1e-4, 1.0, prior='log-uniform')
        }],
    'DT': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__max_depth': Integer(3, 17),
            'regressor_model__min_samples_leaf': Integer(10, 100),
            'regressor_model__min_samples_split': Integer(2, 50),
            'regressor_model__max_features': Categorical(['sqrt', 'log2', None]),
        }
    ],
    'RF': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__n_estimators': Integer(200, 1500),
            'regressor_model__max_depth': Integer(3, 17),
            'regressor_model__min_samples_leaf': Integer(10, 50),
            'regressor_model__min_samples_split': Integer(3, 20),
            'regressor_model__max_features': Categorical(['sqrt', 'log2', None])
        }
    ],
    'GBM': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__n_estimators': Integer(2000, 6000),
            'regressor_model__learning_rate': Real(0.01, 0.05),
            'regressor_model__max_depth': Integer(2, 6),
            'regressor_model__max_features': Categorical(['sqrt']),
            'regressor_model__min_samples_leaf': Integer(10, 20),
            'regressor_model__min_samples_split': Integer(10, 20),
            'regressor_model__loss': Categorical(['huber'])
        }
    ],
    'LGB': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__num_leaves': Integer(5, 20),
            'regressor_model__n_estimators': Integer(2000, 6000),
            'regressor_model__learning_rate': Real(1e-2, 1e-1),
            'regressor_model__verbose': Integer(-10, 10),
            'regressor_model__max_bin': Integer(50, 250),
            'regressor_model__bagging_fraction': Real(0.1, 1),
            'regressor_model__bagging_freq': Integer(2, 10),
            'regressor_model__bagging_seed': Integer(1, 10),
            'regressor_model__feature_fraction': Real(0.1, 1),
            'regressor_model__feature_fraction_seed': Integer(1, 10),
            'regressor_model__objective': Categorical(['regression'])
        }],
    'XGB': [
        {
            'regressor_model__random_state': Categorical([0]),
            'regressor_model__n_estimators': Integer(2000, 6000),
            'regressor_model__learning_rate': Real(0.01, 0.05),
            'regressor_model__max_depth': Integer(2, 6),
            'regressor_model__min_child_weight': Real(0, 0.5),
            'regressor_model__subsample': Real(0.5, 1.0, prior='uniform'),
            'regressor_model__reg_alpha': Real(0.01, 1),
            'regressor_model__reg_lambda': Real(0, 1),
            'regressor_model__gamma': Real(0, 0.05),
            'regressor_model__colsample_bytree': Real(0.2, 1),
            'regressor_model__nthread': Categorical([-1])
        }
    ],
}


@click.command()
@click.option('--model_names_list', required=True, type=str, help='list of models to run')
@click.option('--n_iter', required=True, type=int, help='number of iterations for hyperparameters tuning')
def main(model_names_list, n_iter):
    """
    Runs experiments with BayesSearch for selected models using the specified dataset

    Usage:
    ```
    python run_experiments.py --model_names_list=Lasso,DT,RF,SVR,LGB,GBM,XGB --n_iter=10
    ```
    """
    print('Loading models...')
    model_dict = {}

    dataset = 'model_data.csv'

    try:
        df = pd.read_csv(dataset)
        x = df.drop('price', axis=1)
        y = df['price']

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        for model_name in model_names_list.split(','):
            assert model_name in MODELS_DICT.keys(), f'Unknown model_name: {model_name}'
            model = MODELS_DICT[model_name]
            model_dict[model_name] = model

        for model_name, model in model_dict.items():
            print(f'Running experiments for {model_name}')
            pipe = Pipeline([('scaler', StandardScaler()), ('regressor_model', model)])
            opt = BayesSearchCV(
                pipe,
                MODELS_PARAMS[model_name],
                n_iter=n_iter,
                random_state=7,
                verbose=True
            )
            opt.fit(x_train, y_train)

            best_score = opt.score(x_test, y_test)
            best_params = opt.best_params_

            result_df = pd.DataFrame([{**{'Model': model_name, 'Score': best_score}, **best_params}])
            result_df.to_csv(f'reports/model_results_{model_name}.csv', index=False)

    except Exception as e:
        print(f'An error occurred: {e}')


if __name__ == '__main__':
    main()
