from collections import defaultdict
from graphviz import Digraph
import pandas as pd
import networkx as nx
import copy
import itertools
from .utils import unlist, get_primary_id_from_equivalent_ids, get_name_from_equivalent_ids


def load_res_to_networkx(_res, G, labels, id_mapping, output_id_types):
    """Load restructured API response into a networkx MultiDiGraph

    Params
    ~~~~~~
    G: networkx MultiDiGraph
    _res: restructured API response
    labels: list of schema properties to extract from API response
    id_mapping: dict containing mapping between equivalent ids and original ids
    output_id_types: list of output identifiers
    """
    # check if API response is empty
    if _res:
        # m represent input id, n represent parsed API output
        for m, n in _res.items():
            if n:
                # a represent schema property, b represent value
                for a, b in n.items():
                    if a in labels:
                        for _b in b:
                            if type(_b) != dict:
                                G.add_node(str(_b),
                                           identifier=a,
                                           type=n["@type"],
                                           level=2)
                                G.add_edge(id_mapping[m],
                                           str(_b),
                                           info=None,
                                           label=a)
                            else:
                                for i, j in _b.items():
                                    if i in output_id_types and j:
                                        output_type = _b.get("@type")
                                        source = _b.get("$source")
                                        j = [str(jj) for jj in j]
                                        G.add_nodes_from(j,
                                                         identifier=i,
                                                         type=output_type,
                                                         level=2)
                                        G.add_edge(id_mapping[m],
                                                   str(j[0]),
                                                   info=_b,
                                                   label=a,
                                                   source=source)
    return G


def add_equivalent_ids_to_nodes(G, IDConverter):
    """Add equivalent ids to each node

    Params
    ~~~~~~
    G: Networkx Graph
    IDConverter: Python Class in BTE to convert IDs
    """
    # check if G is empty
    if not G:
        return (G, {})
    # get all nodes which are level 2 (output nodes)
    output_ids = [x for x, y in G.nodes(data=True) if y and y['level'] == 2]
    # check if there is no output nodes
    if not output_ids:
        return (G, {})
    # group output ids based on identifier and type
    idc_inputs = []
    output_ids_dict = defaultdict(list)
    for _id in output_ids:
        type_identifier = G.node[_id]['type'] + ',' + G.node[_id]['identifier']
        output_ids_dict[type_identifier].append(_id)
    # construct inputs for IDConverter
    for k, v in output_ids_dict.items():
        input_cls, input_id = k.split(',')
        idc_inputs.append((v, input_id, input_cls))
    # find equivalent ids
    equivalent_ids = IDConverter.convert_ids(idc_inputs)
    # print("equivalent_ids", equivalent_ids)
    # populate nodes with equivalent ids
    for m, n in equivalent_ids.items():
        # if m.startswith("umls"):
            # print(m, n)
        G.node[m.split(':', 1)[-1]]['equivalent_ids'] = n
    return (G, equivalent_ids)


def merge_two_networkx_graphs(G1, G2):
    """Merge two networkx MultiDiGraphs

    Params
    ------
    G1: networkx graph as the source graph
    G2: networkx graph added to G1
    """
    nodes_to_add = []
    for k, v in G2.nodes(data=True):
        if k not in G1:
            nodes_to_add.append((k, v))
    G1.add_nodes_from(nodes_to_add)
    G1.add_edges_from(G2.edges(data=True))
    return G1


def networkx_to_graphvis(G):
    f = Digraph()
    for k, v, j in G.edges(data=True):
        f.edge(k, v, j['label'])
    return f


def networkx_to_pandas_df(G):
    data = []
    if len(G.nodes()) > 1:
        for k, v, j in G.edges(data=True):
            info = j.get("info")
            pubmed = None
            api = None
            if info:
                pubmed = info.get("bts:pubmed")
                api = info.get("$api")
            source = j.get('source')
            label = j.get('label')
            data.append({'n1': k, 'n1_type': G.nodes[k]['type'],
                         'n2': v, 'n2_type': G.nodes[v]['type'],
                         'predicate': label,
                         'datasource': source,
                         'api': api,
                         'pubmed': pubmed})
    return pd.DataFrame(data)

def retrieve_prop_from_edge(edge_info, prop):
    if prop == 'api':
        data = edge_info['info'].get('$api')
        if data:
            if type(data) != list:
                data = [data]
            return ','.join(data)
    elif prop == 'source':
        data = edge_info['info'].get('$source')
        if data:
            if type(data) != list:
                data = [data]
            return ','.join(data)
    elif prop == 'pubmed':
        data = edge_info['info'].get('bts:pubmed')
        if data:
            if type(data) != list:
                data = [data]
            return ','.join(data)


def connect_networkx_to_pandas_df(G, paths, pred1=None,
                                  intermediate=None,
                                  intermediate_type=None,
                                  pred2=None):
    data = []
    for _path in paths:
        if len(_path) == 3:
            node1_id = get_primary_id_from_equivalent_ids(G.nodes[_path[1]].get('equivalent_ids'), G.nodes[_path[1]]['type'])
            node1_name = get_name_from_equivalent_ids(G.nodes[_path[1]].get('equivalent_ids'))
            start_edges = dict(G[_path[0]][_path[1]]).values()
            end_edges = dict(G[_path[1]][_path[2]]).values()
            for k, v in itertools.product(start_edges, end_edges):
                data.append({'input': _path[0],
                             'input_type': G.nodes[_path[0]]['type'],
                             'pred1': k['label'][4:],
                             'pred1_source': retrieve_prop_from_edge(k, 'source'),
                             'pred1_api': retrieve_prop_from_edge(k, 'api'),
                             'pred1_pubmed': retrieve_prop_from_edge(k, 'pubmed'),
                             'node1_id': node1_id,
                             'node1_name': node1_name,
                             'node1_type': G.nodes[_path[1]]['type'],
                             'pred2': v['label'][4:],
                             'pred2_source': retrieve_prop_from_edge(v, 'source'),
                             'pred2_api': retrieve_prop_from_edge(v, 'api'),
                             'pred2_pubmed': retrieve_prop_from_edge(v, 'pubmed'),
                             'output': _path[2],
                             'output_type': G.nodes[_path[2]]['type']})
        else:
            edges = G[_path[0]][_path[1]]
            for _edge in edges.values():
                data.append({'input': _path[0],
                             'input_type': G.nodes[_path[0]]['type'],
                             'pred1': _edge['label'],
                             'pred1_source': retrieve_prop_from_edge(_edge, 'source'),
                             'pred1_api': retrieve_prop_from_edge(_edge, 'api'),
                             'pred1_pubmed': retrieve_prop_from_edge(_edge, 'pubmed'),
                             'output': _path[1],
                             'output_type': G.nodes[_path[1]]['type'],
                             })
    df = pd.DataFrame(data)
    if pred1:
        df = df[(df['pred1'] == pred1)]
    if intermediate:
        df = df[(df['intermediate'] == intermediate)]
    if intermediate_type:
        df = df[(df['intermediate_type'] == intermediate_type)]
    if pred2:
        df = df[(df['pred2'] == pred2)]
    return df


def predict_networkx_to_pandas_df(G, paths, path_length):
    """Convert the networkx graph from the predict query into pandas table
    
    params
    ------
    G: the networkx multidigraph from the query
    paths: all paths connecting from start to end
    path_length: the length of the query path
    """
    data = []
    for _path in paths:
        info = {'input': _path[0],
                'input_type': G.nodes[_path[0]]['type'],
                'output': _path[-1],
                'output_type': G.nodes[_path[-1]]['type']}
        for i in range(1, len(_path) - 1):
            start_edges = dict(G[_path[i-1]][_path[i]]).values()
            end_edges = dict(G[_path[1]][_path[2]]).values()

        if len(_path) == 3:
            node1_id = get_primary_id_from_equivalent_ids(G.nodes[_path[1]].get('equivalent_ids'), G.nodes[_path[1]]['type'])
            node1_name = get_name_from_equivalent_ids(G.nodes[_path[1]].get('equivalent_ids'))
            start_edges = dict(G[_path[0]][_path[1]]).values()
            end_edges = dict(G[_path[1]][_path[2]]).values()
            for k, v in itertools.product(start_edges, end_edges):
                data.append({'input': _path[0],
                             'input_type': G.nodes[_path[0]]['type'],
                             'pred1': k['label'][4:],
                             'pred1_source': retrieve_prop_from_edge(G, 'source',
                                                                _path[0],
                                                                _path[1]),
                             'pred1_api': retrieve_prop_from_edge(G, 'api',
                                                                _path[0],
                                                                _path[1]),
                             'pred1_pubmed': retrieve_prop_from_edge(G, 'pubmed',
                                                                _path[0],
                                                                _path[1]),
                             'node1_id': node1_id,
                             'node1_name': node1_name,
                             'node1_type': G.nodes[_path[1]]['type'],
                             'pred2': v['label'][4:],
                             'pred2_source': retrieve_prop_from_edge(G, 'source',
                                                                _path[1],
                                                                _path[2]),
                             'pred2_api': retrieve_prop_from_edge(G, 'api',
                                                                _path[1],
                                                                _path[2]),
                             'pred2_pubmed': retrieve_prop_from_edge(G, 'pubmed',
                                                                _path[1],
                                                                _path[2]),
                             'output': _path[2],
                             'output_type': G.nodes[_path[2]]['type']})
        else:
            edges = G[_path[0]][_path[1]]
            for _edge in edges:
                data.append({'input': _path[0],
                             'input_type': G.nodes[_path[0]]['type'],
                             'pred1': _edge['label'],
                             'source1': retrieve_prop_from_edge(G, 'source',
                                                                _path[0],
                                                                _path[1]),
                             'api1': retrieve_prop_from_edge(G, 'api',
                                                                _path[0],
                                                                _path[1]),
                             'output': _path[1],
                             'output_type': G.nodes[_path[1]]['type'],
                             })
    df = pd.DataFrame(data)
    if pred1:
        df = df[(df['pred1'] == pred1)]
    if intermediate:
        df = df[(df['intermediate'] == intermediate)]
    if intermediate_type:
        df = df[(df['intermediate_type'] == intermediate_type)]
    if pred2:
        df = df[(df['pred2'] == pred2)]
    return df




def networkx_json_to_visjs(res):
    """Convert JSON output from networkx to visjs compatible version

    Params
    ------
    res: JSON output from networkx of the graph
    """
    colors = {1: 'green', 2: 'red', 3: 'rgba(255,168,7)'}
    if res:
        links = res['links']
        new_links = []
        for _link in links:
            _link['from'] = _link.pop('source')
            _link['to'] = _link.pop('target')
            _link['font'] = {'align': 'middle'}
            _link['arrows'] = 'to'
            new_links.append(_link)
        res['links'] = new_links
        new_nodes = []
        for _node in res['nodes']:
            _node['label'] = _node['identifier'][4:] + ':' + str(_node['id'])
            _node['color'] = colors[_node['level']]
            if 'equivalent_ids' in _node:
                equ_ids = []
                for k, v in _node['equivalent_ids'].items():
                    if isinstance(v, list):
                        for _v in v:
                            equ_ids.append(k + ':' + str(_v))
                    else:
                        equ_ids.append(k + ":" + str(v))
                equ_ids = '<br>'.join(equ_ids)
                _node['equivalent_ids'] = equ_ids
            new_nodes.append(_node)
        res['nodes'] = new_nodes
    return res
