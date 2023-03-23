from treelib import Tree
import pydot
import graphviz

from treelib import Tree, Node
import sys
import subprocess
import pydot


def show1(file_name):
    
    f = open(file_name,'r')
    
    lines = f.readlines()
    f.close()
    tree=Tree()
    
    for line in lines:
        line=line.strip().split()
        # print("Hello")
        if line[1] == '-1':
            tree.create_node(line[2],line[0])
        else:
            # tree.create_node(str(line[2]),line[0],line[1])
            tree.create_node(str(line[2])+"\n"+str(line[0]),line[0],line[1])

        # if line[3] == '0':
        #     node = tree.get_node(line[0])
        #     node.set_node_style('filled', 'lightblue')                
            
    tree.to_graphviz(file_name[:-3]+"dot")
    # output=subprocess.check_output(['dot','-Tpdf',file_name[:-3]+"dot"])
    
    # f = open(file_name[:-3]+"pdf",'wb')
    # f.write(output)
    # f.close()

    (graph,) = pydot.graph_from_dot_file(file_name[:-3]+"dot")
    graph.write_png(file_name[:-3]+'png')

    # subprocess.check_call(['rm','temp.dot'])
    # subprocess.check_call(['rm',file_name])

def show(file_name):
    f = open(file_name, 'r')
    lines = f.readlines()
    f.close()
    tree = Tree()

    for line in lines:
        line = line.strip().split()
        if line[1] == '-1':
            if line[3] == '0':
                tree.create_node(line[2], line[0], data={'color': 'red'})
            else:
                tree.create_node(line[2], line[0], data={'color': 'green'})
        else:
            if line[3] == '0':
                tree.create_node(f"{line[2]}\n{line[0]}\n{line[3]}", line[0], line[1], data={'color': 'red'})
            else:
                tree.create_node(f"{line[2]}\n{line[0]}\n{line[3]}", line[0], line[1], data={'color': 'green'})

    dot = graphviz.Digraph(comment='Tree')
    for node in tree.all_nodes():
        color = node.data.get('color')
        if color:
            dot.node(node.identifier, label=node.tag, color=color, style='filled')
        else:
            dot.node(node.identifier, label=node.tag)

    for node in tree.all_nodes():
        for child_id in tree.children(node.identifier):
            # print(node.identifier,child_id)
            dot.edge(node.identifier, child_id.identifier)

    dot.render(file_name[:-3] + 'dot', view=False)
    (graph,) = pydot.graph_from_dot_file(file_name[:-3] + 'dot')
    graph.write_png(file_name[:-3] + 'png')
