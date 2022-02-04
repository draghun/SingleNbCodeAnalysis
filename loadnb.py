import json
import ast
import numpy as np

from funccalls import FuncCallVisitor

## Read notebook file, load to dictionary
def load_nb_json(filename):
    raw_nb = {}
    with open(filename, 'r') as json_file:
        raw_nb = json.load(json_file)
        json_file.close()

    return raw_nb

## isolate the code cells and return it 
def get_code_cells(cells):
    nb_code_cells = dict() # outputting code cells
    nb_code_str_cells = dict()

    # for each cell is list of cells
    for i, cell in enumerate(cells):
        if isinstance(cell, dict):
            cell_keys = cell.keys()
        else:
            cell_keys = []

        if "cell_type" in cell_keys:
            cell_type = cell["cell_type"]
        else:
            cell_type = None

        # if cell type is code
        if cell_type == "code":
            src = list()

            cell_key = None
            if "source" in cell_keys:
                cell_key = "source"
            elif "input" in cell_keys:
                cell_key = "input"

            if cell_key != None:
                src = cell[cell_key]

                if isinstance(src, list):
                    nb_code_cells[i] = src
                else:
                    nb_code_cells[i] = [src]

                cell_str_content = ''
                for s in src:
                    s = s.replace('\n', '')
                    if (len(s) > 0):
                        cell_str_content = cell_str_content + s + '\n'
                
                if (len(cell_str_content) > 0):
                    print("CELL: " + cell_str_content)
                    nb_code_str_cells[i] = cell_str_content

    return nb_code_str_cells

## get all the function calls in the cell
def get_func_calls(tree):
    func_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callvisitor = FuncCallVisitor()
            callvisitor.visit(node.func)
            func_calls.append(callvisitor.name)

    return func_calls

def parse_nb(raw_nb):
    code_cells = {}
    trees = []
    cell_vars = []
    cell_funcs = []
    cell_invos = []

    if isinstance(raw_nb, dict):
        keys = raw_nb.keys()
    else:
        keys = []

    if ("cells" in keys):
        code_cells = get_code_cells(raw_nb["cells"])
        
        for cell in code_cells:
            # get the ast
            tree = ast.parse(code_cells[cell])
            trees.append(tree)

            # get variables from ast
            cell_var = sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Load)})
            print(cell_var)
            cell_vars.append(cell_var)

            # get function definitions from ast
            cell_invo = get_func_calls(tree)
            print(cell_invo)
            cell_invos.append(cell_invo)

            # get function calls from ast
            cell_func = [x.name for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)]
            print(cell_func)
            cell_funcs.append(cell_func)

    return (cell_vars, cell_funcs, cell_invos)

# count the number of times a variable has been called or redefined 
def count_var_edges(nb_vars):
    connections = []
    for i, cell in enumerate(nb_vars):
        count = 0
        for v in cell: 
            for j, other_cell in enumerate(nb_vars):
                if (not i == j and v in other_cell):
                    count += 1
        connections.append(count / len(nb_vars))
    
    con_np = np.array(connections)
    norm_score = con_np.mean()
    
    return connections, norm_score

# count the number of times a local function has been invoked
def count_func_edges(nb_funcs, nb_invos):
    connections = []
    for i, cell in enumerate(nb_funcs):
        count = 0
        for v in cell: 
            for j, other_cell in enumerate(nb_invos):
                if (v in other_cell):
                    count += 1
        connections.append(count / len(nb_funcs))
    
    con_np = np.array(connections)
    norm_score = con_np.mean()
    
    return connections, norm_score

# main
if __name__ == "__main__":
    raw_nb = load_nb_json('sample_1.ipynb')
    nb_vars, nb_funcs, nb_invos = parse_nb(raw_nb)
    var_con, var_score = count_var_edges(nb_vars)
    func_con, func_score = count_func_edges(nb_funcs, nb_invos)

    print(var_con, func_con)

    sum_con = [0] * len(var_con)
    for i in range(len(var_con)):
        sum_con[i] = var_con[i] + func_con[i]

    print(sum_con)

    sum_con_np = np.array(sum_con)
    norm_score = sum_con_np.mean()

    print(var_score, func_score, norm_score)