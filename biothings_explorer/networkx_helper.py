from collections import defaultdict


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
    # populate nodes with equivalent ids
    for m, n in equivalent_ids.items():
        G.node[m.split(':', 1)[-1]]['equivalent_ids'] = n
    return (G, equivalent_ids)


def merge_two_networkx_graphs(G1, G2):
    """Merge two networkx MultiDiGraphs

    Params
    ------
    G1: networkx graph as the source graph
    G2: networkx graph added to G1
    """
    G1.add_nodes_from(G1.nodes(data=True))
    G1.add_edges_from(G2.edges(data=True))
    return G1


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
