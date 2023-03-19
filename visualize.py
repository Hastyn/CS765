from treelib import Tree, Node
import sys
import subprocess
import pydot


def show(file_name):
    
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
    graph.write_png(file_name[:-3]+'.png')

    # subprocess.check_call(['rm','temp.dot'])
    # subprocess.check_call(['rm',file_name])
    