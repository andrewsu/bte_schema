import unittest
from biothings_explorer.registry import Registry
from biothings_explorer.user_query_dispatcher import SingleEdgeQueryDispatcher


class TestSingleHopQuery(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()

    def test_interactswith(self):
        # test <chemical, interactswith, anatomy>
        seqd = SingleEdgeQueryDispatcher(input_cls='ChemicalSubstance',
                                         input_id='bts:umls',
                                         output_cls='AnatomicalEntity',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0076241',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0233929' in seqd.G)
        seqd = SingleEdgeQueryDispatcher(input_cls='AnatomicalEntity',
                                         input_id='bts:umls',
                                         output_cls='ChemicalSubstance',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0233929',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0076241' in seqd.G)
        # test <chemical, interactswith, anatomy>
        seqd = SingleEdgeQueryDispatcher(input_cls='ChemicalSubstance',
                                         input_id='bts:umls',
                                         output_cls='AnatomicalEntity',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0038467',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0042018' in seqd.G)
        seqd = SingleEdgeQueryDispatcher(input_cls='AnatomicalEntity',
                                         input_id='bts:umls',
                                         output_cls='ChemicalSubstance',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0042018',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0038467' in seqd.G)
        # test <chemical, interactswith, anatomy>
        seqd = SingleEdgeQueryDispatcher(input_cls='ChemicalSubstance',
                                         input_id='bts:umls',
                                         output_cls='AnatomicalEntity',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0002151',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0032105' in seqd.G)
        seqd = SingleEdgeQueryDispatcher(input_cls='AnatomicalEntity',
                                         input_id='bts:umls',
                                         output_cls='ChemicalSubstance',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0032105',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0002151' in seqd.G)
        # test <chemical, interactswith, bp>
        seqd = SingleEdgeQueryDispatcher(input_cls='ChemicalSubstance',
                                         input_id='bts:umls',
                                         output_cls='BiologicalProcess',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C0885444',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C1158226' in seqd.G)
        seqd = SingleEdgeQueryDispatcher(input_cls='AnatomicalEntity',
                                         input_id='bts:umls',
                                         output_cls='ChemicalSubstance',
                                         output_id='bts:umls',
                                         pred='bts:associatedWith',
                                         values='C1158226',
                                         registry=self.reg)
        seqd.query()
        self.assertTrue('C0885444' in seqd.G)