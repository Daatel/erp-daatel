import inspect
import database

source = inspect.getsource(database.gerar_comissao_se_necessario)
print(source)
