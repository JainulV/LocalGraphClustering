from localgraphclustering import *
import time
import numpy as np

def load_example_graph(vtype,itype):
    return GraphLocal("localgraphclustering/tests/data/dolphins.edges",separator=" ",vtype=vtype,itype=itype)

def test_GraphLocal_methods():
    g = load_example_graph(np.uint32,np.uint32)
    g.largest_component()
    g.biconnected_components()
    g.core_number()
    ei,ej,e = [],[],[]
    for i in range(g._num_vertices):
        for j in range(g.ai[i],g.ai[i+1]):
            ei.append(i)
            ej.append(g.aj[j])
            e.append(g.adjacency_matrix.data[j])
    g1 = GraphLocal()
    g1.list_to_gl(ei,ej,e)

    assert(np.array_equal(g1.ai,g.ai))
    assert(np.array_equal(g1.aj,g.aj))
    assert(np.array_equal(g1.adjacency_matrix.data,g.adjacency_matrix.data))

    g1.discard_weights()

    # Compute triangle clusters and cluster metrics
    cond,cut,vol,cc,t = triangleclusters(g)
    minverts, minvals = g.local_extrema(cond,True)
    print("vertices with minimum conductance neighborhood:",minverts)

    # Test graph with more than one components
    G = GraphLocal("notebooks/datasets/neuro-fmri-01.edges",file_type = "edgelist", separator = " ", header = True)

def test_sweepcut_self_loop():
    """ This is a regression test for sweep-cuts with self-loops """
    g = GraphLocal()
    # make a graph with a triangle that has a self-loop on one Vertex
    # connected to a lot of other vertices and where there are lots
    # of other things connected as well...
    #g.list_to_gl([0,0,1,2,2,2,2],[1,2,2,2])
    import networkx as nx
    G = nx.Graph()
    K6uK3 = nx.complete_graph(6)
    K6uK3.add_edge(5,6)
    K6uK3.add_edge(5,7)
    K6uK3.add_edge(6,7)
    K6uK3.add_edge(5,5)
    gloop = GraphLocal().from_networkx(K6uK3)
    S = [5,6,7]
    w = [3,2,1]
    Sp,phi1 = sweep_cut(gloop,(S,np.array(w)))
    assert(set(S) == set(Sp))
    assert(phi1 == 5/12)
    assert(phi1 == gloop.set_scores(S)["cond"])

def setup_fiedler_test(g):
    output_sp = fiedler(g)
    R = [1]
    R.extend(g.neighbors(R[0]))
    output_sp2 = fiedler_local(g,R)
    assert(np.all(output_sp2[0][1] >= -1.0e-6)) # make sure everything is almost positive.

def setup_fiedler_local_test(g):
    R = [1]
    R.extend(g.neighbors(R[0]))
    phi0 = g.set_scores(R)["cond"]
    sparse_vec = fiedler_local(g,R)[0]
    S = sweep_cut(g,sparse_vec)[0]
    phi1 = g.set_scores(S)["cond"]
    assert(phi1 <= phi0)

def setup_sweep_cut_test(g):
    tmp1 = sweep_cut(g,([1,2,3,4,5,6,7,8,9],[1,2,3,4,5,6,7,8,9]),cpp=False)
    tmp2 = sweep_cut(g,([1,2,3,4,5,6,7,8,9],[1,2,3,4,5,6,7,8,9]))
    assert(tmp1[1]==tmp2[1])

def setup_spectral_clustering_test(g):
    output_sp = fiedler(g)
    R = [1]
    R.extend(g.neighbors(R[0]))
    insize = len(R)
    output_sp2 = spectral_clustering(g,R,method="fiedler_local")[0]
    Z = set(R).union(output_sp2)
    assert(len(Z) == insize)
    phi0 = g.set_scores(R)["cond"]
    for method in ["fiedler_local","acl","l1reg","nibble"]:
        phi = g.set_scores(spectral_clustering(g, R, method=method)[0])["cond"]
        assert(phi <= phi0)

def setup_flow_clustering_test(g):
    # Call the global spectral partitioning algorithm.
    output_sp = fiedler(g)
    eig2 = output_sp

    # Round the eigenvector
    output_sc = sweep_cut(g,eig2)

    # Extract the partition for g and store it.
    R = output_sc[0]
    phi0 = g.set_scores(R)["cond"]

    for method in ["mqi","crd","sl"]:
        phi = g.set_scores(flow_clustering(g,R,method=method)[0])["cond"]
        assert(phi <= phi0)

def test_all_algs():
    for vtype,itype in [(np.uint32,np.uint32),(np.uint32,np.int64),(np.int64,np.int64)]:
        g = load_example_graph(vtype,itype)
        setup_fiedler_test(g)
        setup_fiedler_local_test(g)
        setup_sweep_cut_test(g)
        setup_spectral_clustering_test(g)
        setup_flow_clustering_test(g)
