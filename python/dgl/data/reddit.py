from __future__ import absolute_import

import scipy.sparse as sp
import numpy as np
import os, sys
from .utils import download, extract_archive, get_download_dir, _get_dgl_url
from ..utils import retry_method_with_fix
from .. import backend as F
from .. import convert

class RedditDataset(object):
    def __init__(self, self_loop=False):
        download_dir = get_download_dir()
        self_loop_str = ""
        if self_loop:
            self_loop_str = "_self_loop"
        zip_file_path = os.path.join(download_dir, "reddit{}.zip".format(self_loop_str))
        extract_dir = os.path.join(download_dir, "reddit{}".format(self_loop_str))
        self._url = _get_dgl_url("dataset/reddit{}.zip".format(self_loop_str))
        self._zip_file_path = zip_file_path
        self._extract_dir = extract_dir
        self._self_loop_str = self_loop_str
        self._load()

    def _download(self):
        download(self._url, path=self._zip_file_path)
        extract_archive(self._zip_file_path, self._extract_dir)

    @retry_method_with_fix(_download)
    def _load(self):
        # graph
        coo_adj = sp.load_npz(os.path.join(
            self._extract_dir, "reddit{}_graph.npz".format(self._self_loop_str)))
        self.graph = convert.graph(coo_adj)
        # features and labels
        reddit_data = np.load(os.path.join(self._extract_dir, "reddit_data.npz"))
        self.features = reddit_data["feature"]
        self.labels = reddit_data["label"]
        self.num_labels = 41
        # tarin/val/test indices
        node_types = reddit_data["node_types"]
        self.train_mask = (node_types == 1)
        self.val_mask = (node_types == 2)
        self.test_mask = (node_types == 3)

        print('Finished data loading.')
        print('  NumNodes: {}'.format(self.graph.number_of_nodes()))
        print('  NumEdges: {}'.format(self.graph.number_of_edges()))
        print('  NumFeats: {}'.format(self.features.shape[1]))
        print('  NumClasses: {}'.format(self.num_labels))
        print('  NumTrainingSamples: {}'.format(len(np.nonzero(self.train_mask)[0])))
        print('  NumValidationSamples: {}'.format(len(np.nonzero(self.val_mask)[0])))
        print('  NumTestSamples: {}'.format(len(np.nonzero(self.test_mask)[0])))

    def __getitem__(self, idx):
        assert idx == 0, "Reddit Dataset only has one graph"
        self.graph.ndata['train_mask'] = F.tensor(self.train_mask, dtype=F.bool)
        self.graph.ndata['val_mask'] = F.tensor(self.val_mask, dtype=F.bool)
        self.graph.ndata['test_mask'] = F.tensor(self.test_mask, dtype=F.bool)
        self.graph.ndata['feat'] = F.tensor(self.features, dtype=F.float32)
        self.graph.ndata['label'] = F.tensor(self.labels, dtype=F.int64)
        return self.graph
    
    def __len__(self):
        return 1
