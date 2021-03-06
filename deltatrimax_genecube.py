# -*- coding: utf-8 -*-
"""Delta Trimax Triclustering on the Gene Cube.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1fh5hmJp-PzYHU5s0v7veMc82fP63tKBR

# Data
"""

import pandas as pd
from io_methods import read_data_from_excel

data = pd.read_excel('GSE7476.xlsx')

newlbl = data.iloc[0].copy()
newlbl[0] = 'ID Gen'
newlbl[1] = 'Simbol Gen'
newlbl[2] = 'Kromosom'
data.columns = newlbl.values

data = data.iloc[2:]

data['Kromosom'] = data['Kromosom'].map({1: 1, 2: 2, 3: 3,
                                         4: 4, 5: 5, 6: 6, 7: 7,
                                         8: 8, 9: 9, 10: 10, 11: 11,
                                         12: 12, 13: 13, 14: 14,
                                         15: 15, 16: 16, 17: 17,
                                         18: 18, 19: 19, 20: 20,
                                         21: 21, 22: 22, 'X': 23,
                                         'Y': 24})

new_symbols = []
for symbol in data['Simbol Gen'].values:
    new_symbols.append(symbol.partition('///')[0])
data['Simbol Gen'] = new_symbols

newind1 = data['ID Gen'].values.copy()
newind2 = data['Simbol Gen'].values.copy()

import numpy as np

data.index = [np.arange(len(data.values)), newind1, newind2]
data.index.names = ['index', 'ID Gen', 'Simbol Gen']
data.drop('ID Gen', axis=1, inplace=True)
data.drop('Simbol Gen', axis=1, inplace=True)

data = data.astype(float)

data.head()

data.shape

grouped_kromosom = data.groupby('Kromosom', sort=False)

"""# Formation of the 3D Array"""

import numpy as np
from scipy.spatial import distance


class Array3D():
    def __init__(self, X, indices=None):
        if (X is None):
            raise Exception("Error: No data provided!")
        else:
            self.X = X.copy()
            self.array3D_size = max([self.X[x].shape[0] for x in range(len(self.X))])
            self.indices = indices.copy()

    def _group_gen(self, kromosom):
        distances = np.ma.masked_array(distance.cdist(self.X[kromosom],
                                                      self.sets,
                                                      self.metric))

        n_gen_kromosom = self.X[kromosom].shape[0]
        n_gen_prev = self.sets.shape[0]
        gen_kromosom = np.array([-1] * n_gen_kromosom)
        gen_prev = np.array([-1] * n_gen_prev)
        n_iterasi = min(n_gen_kromosom, n_gen_prev)
        for i in range(n_iterasi):
            closest = np.unravel_index(distances.argmin(), distances.shape)
            distances[closest[0], :] = np.ma.masked
            distances[:, closest[1]] = np.ma.masked

            if (self.method == 'centroids'):
                self.centroids[closest[1]].append((kromosom, closest[0]))
            self.sets[closest[1]] = self.X[kromosom][closest[0]]
            gen_kromosom[closest[0]] = closest[1]
            gen_prev[closest[1]] = closest[0]

        if (n_gen_kromosom > n_gen_prev):
            gen_left = np.where(gen_kromosom == -1)[0]
            self.sets = np.vstack((self.sets,
                                   self.X[kromosom].take(gen_left, axis=0)))
            if (self.method == 'centroids'):
                set_id = n_gen_prev
                for gen_left in gen_left:
                    self.centroids[set_id].append((kromosom, gen_left))
                    set_id += 1

        new_slice = self.sets.copy()
        new_slice[np.where(gen_prev == -1)] = [np.nan] * self.X[kromosom].shape[1]
        self.array3D = np.dstack((self.array3D, new_slice))

        if (self.indices is not None):
            if (n_gen_kromosom > n_gen_prev):
                kromosom_ind = np.append(gen_prev, gen_left).tolist()
            else:
                kromosom_ind = gen_prev.tolist()
            for i in range(len(kromosom_ind)):
                if (kromosom_ind[i] != -1):
                    kromosom_ind[i] = self.indices[kromosom][kromosom_ind[i]]
                else:
                    kromosom_ind[i] = None
            self.indices3D += [kromosom_ind]

    def _reevaluate_centroids(self):
        new_centroids = []

        for set_id in self.centroids.keys():
            set_centroid = []
            for set_gen in self.centroids[set_id]:
                set_centroid.append(self.X[set_gen[0]][set_gen[1]])
            new_centroids.append(np.mean(np.asarray(set_centroid), axis=0))

        self.sets = np.asarray(new_centroids)

    def create(self, metric='euclidean', method='centroids'):
        self.metric = metric
        self.method = method

        self.sets = np.array(self.X[0])
        self.array3D = self.X[0]
        if (self.indices is not None):
            self.indices3D = [self.indices[0]]
        else:
            self.indices3D = None

        padding = np.array(self.X[0].shape[1] * [np.nan])[np.newaxis, :]
        for i in range(self.array3D_size - self.X[0].shape[0]):
            self.array3D = np.vstack((self.array3D, padding))

        if (method == 'onebyone'):
            for i in range(1, len(self.X)):
                self._group_gen(i)
        else:
            self.centroids = {}
            for i in range(self.array3D_size):
                if (i < self.X[0].shape[0]):
                    self.centroids[i] = [(0, i)]
                else:
                    self.centroids[i] = []
            for i in range(1, len(self.X)):
                self._group_gen(i)
                self._reevaluate_centroids()

        self.array3D = self.array3D.swapaxes(0, 2)
        self.array3D = self.array3D.swapaxes(1, 2)

        return self.array3D, self.indices3D

kromosom_grouped = []
indices = []
for kromosom in range(1, 25):
    kromosom_grouped.append(grouped_kromosom.get_group(kromosom).iloc[:, 1:].values.copy())
    indices.append(grouped_kromosom.get_group(kromosom).index.tolist())

arr, ind = Array3D(kromosom_grouped, indices=indices).create(method='centroids')

arr.shape

print(arr)

"""# Delta Trimax"""

import numpy as np
import sys
import time

import warnings

class DeltaTrimax():
    def __init__(self,D):
        self.D = D.copy()
        self.D_asli = D.copy()
    
    def hitung_MSR(self, gen, sampel, kromosom, g_add=False, s_add=False, c_add=False):
        
        gen_idx = np.expand_dims(np.expand_dims(np.nonzero(gen)[0], axis=0), axis=2)
        #
        kromosom_idx = np.expand_dims(np.expand_dims(np.nonzero(kromosom)[0], axis=1), axis=1)
        #
        sampel_idx = np.expand_dims(np.expand_dims(np.nonzero(sampel)[0], axis=0), axis=0)
            
        subarr = self.D[kromosom_idx, gen_idx, sampel_idx]
        self.n_gen = subarr.shape[1]
        self.n_sampel = subarr.shape[2]
        self.n_kromosom = subarr.shape[0]
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
        
        # hitung m_gSC (gen)
            m_gSC = np.nanmean(np.nanmean(subarr, axis=2),axis=0)
            m_gSC = np.expand_dims(np.expand_dims(m_gSC, axis=0), axis=2)
        
        # hitung m_GsC (sampel)
            m_GsC = np.nanmean(np.nanmean(subarr, axis=0), axis=0)
            m_GsC = np.expand_dims(np.expand_dims(m_GsC, axis=0), axis=1)
        
        # hitung m_GSc (kromosom)
            m_GSc = np.nanmean(np.nanmean(subarr, axis=2), axis=1)
            m_GSc = np.expand_dims(np.expand_dims(m_GSc, axis=1), axis=2)
            
        # hitung m_GSC
            m_GSC = np.nanmean(subarr)
        
        # hitung MSR
            residue = subarr - m_gSC - m_GsC - m_GSc + (2*m_GSC)
            SR = np.square(residue)
            
            self.MSR = np.nanmean(SR)
            self.MSR_gen = np.nanmean(np.nanmean(SR, axis=2), axis=0)
            self.MSR_sampel = np.nanmean(np.nanmean(SR, axis=0), axis=0)
            self.MSR_kromosom = np.nanmean(np.nanmean(SR, axis=2), axis=1)
            
            if g_add:
                non_gen = np.expand_dims(np.expand_dims(np.nonzero(gen==0)[0],axis=0),axis=2)
            
            # hitung m_gSC (untuk gen yang bukan tricluster dari data asli)
                D_b = self.D.copy()
                D_b[kromosom_idx, non_gen, sampel_idx] = self.D_asli[kromosom_idx, non_gen, sampel_idx]

                subarr_b = D_b[kromosom_idx, non_gen, sampel_idx]

                m_gSC_b = np.nanmean(np.nanmean(subarr_b,axis=2),axis=0)
                m_gSC_b = np.expand_dims(np.expand_dims(m_gSC_b,axis=0),axis=2)

                r = subarr_b - m_gSC_b - m_GsC - m_GSc + (2*m_GSC)
                sr_b = np.square(r)
                self.MSR_gen_b = np.nanmean(np.nanmean(sr_b,axis=2),axis=0)
            
        
            if s_add:
                non_sampel = np.expand_dims(np.expand_dims(np.nonzero(sampel==0)[0],axis=0),axis=0)
            
                # hitung m_GsC (untuk sampel yg bukan tricluster)
                D_b = self.D.copy()
                D_b[kromosom_idx,gen_idx, non_sampel] = self.D_asli[kromosom_idx, gen_idx, non_sampel]
                subarr_b = D_b[kromosom_idx, gen_idx, non_sampel]

                m_GsC_b = np.nanmean(np.nanmean(subarr_b,axis=0), axis=0)
                m_GsC_b = np.expand_dims(np.expand_dims(m_GsC_b,axis=0),axis=1)
            
                r = subarr_b - m_gSC - m_GsC_b - m_GSc + (2*m_GSC)
                sr_b = np.square(r)
                self.MSR_sampel_b = np.nanmean(np.nanmean(sr_b,axis=0),axis=0)
        
            if c_add:
                non_kromosom = np.expand_dims(np.expand_dims(np.nonzero(kromosom==0)[0],axis=1),axis=1)
            
                # hitung m_GSc (untuk kromosom yg bukan tricluster)
                D_b = self.D.copy()
                D_b[non_kromosom, gen_idx, sampel_idx] = self.D_asli[non_kromosom, gen_idx, sampel_idx]
                subarr_b = D_b[non_kromosom, gen_idx, sampel_idx]

                m_GSc_b = np.nanmean(np.nanmean(subarr_b,axis=2),axis=1)
                m_GSc_b = np.expand_dims(np.expand_dims(m_GSc_b,axis=1),axis=2)

                r = subarr_b - m_gSC - m_GsC - m_GSc_b + (2*m_GSC)
                sr_b = np.square(r)
                self.MSR_kromosom_b = np.nanmean(np.nanmean(sr_b,axis=2),axis=1)
        
    def multiple_node_deletion(self, gen, sampel, kromosom):
        self.hitung_MSR(gen, sampel, kromosom)
        #i = 1
        self.muldel = 1
        while (self.MSR > self.delta):
            #print("mnd ke", i,"--MSR",self.MSR)
            hapus = 0
            
            # hapus gen
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                if (self.n_gen > self.gen_cutoff):
                    gen_dihapus = self.MSR_gen > (self.MSR * self.lamda)
                    nonz_idx = gen.nonzero()[0]
                    if (gen_dihapus.any()):
                        hapus = 1
                    gen.put(nonz_idx[gen_dihapus],0)
                
            # hapus sampel
                if (self.n_sampel > self.sampel_cutoff):
                    sampel_dihapus = self.MSR_sampel > (self.MSR * self.lamda)
                    nonz_idx = sampel.nonzero()[0]
                    if (sampel_dihapus.any()):
                        hapus = 1
                    sampel.put(nonz_idx[sampel_dihapus],0)

            # hapus kromosom
                if (self.n_kromosom > self.kromosom_cutoff):
                    kromosom_dihapus = self.MSR_kromosom > (self.MSR * self.lamda)
                    nonz_idx = kromosom.nonzero()[0]
                    if kromosom_dihapus.any():
                        hapus = 1
                    kromosom.put(nonz_idx[kromosom_dihapus],0)

            # menghentikan iterasi
            if not hapus:
                break
            
            sys.stdout.write('\r multiple deletion {} - single deletion {} - node addition {}'.format(
                self.muldel, self.singdel, self.nodeadd
            ))
            sys.stdout.flush()

            #i += 1
            self.muldel += 1
            self.hitung_MSR(gen, sampel, kromosom)
       
        #print("MSR akhir multiple node addition :",self.MSR)
        return gen, sampel, kromosom
  
    def single_node_deletion(self, gen, sampel, kromosom):
        self.hitung_MSR(gen, sampel, kromosom)
        #print("MSR awal snd",self.MSR)
        #i = 1
        self.singdel = 1
        while (self.MSR > self.delta):
            #print("snd ke-", i, "---MSR",self.MSR)
            
            gen_idx = np.nanargmax(self.MSR_gen)
            sampel_idx = np.nanargmax(self.MSR_sampel)
            kromosom_idx = np.nanargmax(self.MSR_kromosom)
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                if (self.MSR_gen[gen_idx] > self.MSR_sampel[sampel_idx]):
                    if (self.MSR_gen[gen_idx] > self.MSR_kromosom[kromosom_idx]):
                        # hapus gen
                        nonz_idx = gen.nonzero()[0]
                        # print("menghapus gen ke-", gen_max)
                        gen.put(nonz_idx[gen_idx], 0)
                    else:
                        # hapus kromosom
                        nonz_idx = kromosom.nonzero()[0]
                        kromosom.put(nonz_idx[kromosom_idx], 0)
                        # print("menghapus kromosom ke-", kromosom_max)
                else:
                    if (self.MSR_sampel[sampel_idx] > self.MSR_sampel[sampel_idx]):
                        # hapus sampel
                        nonz_idx = sampel.nonzero()[0]
                        sampel.put(nonz_idx[sampel_idx],0)
                        # print("menghapus sampel ke-", sampel_max)
                    else:
                        # hapus kromosom
                        nonz_idx = kromosom.nonzero()[0]
                        kromosom.put(nonz_idx[kromosom_idx],0)
                        # print("menghapus kromosom ke-", kromosom_max)
            
                sys.stdout.write('\r multiple deletion {} - single deletion {} - node addition {}'.format(
                    self.muldel, self.singdel, self.nodeadd
                ))
                sys.stdout.flush()
            
            # i+=1
                self.singdel += 1
                self.hitung_MSR(gen, sampel, kromosom)


        #print("MSR akhir single node deletion :", self.MSR)
        return gen, sampel, kromosom
                    
    def node_addition(self, gen, sampel, kromosom):
        # print("MSR awal node addition :",self.MSR)
        # i = 1
        self.nodeadd = 1
        while True:
            # print("node addition ke-",i)
            
            self.hitung_MSR(gen, sampel, kromosom)
            n_kromosom = np.count_nonzero(kromosom)
            n_gen = np.count_nonzero(gen)
            n_sampel = np.count_nonzero(sampel)
            
            # penambahan gen
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                self.hitung_MSR(gen, sampel, kromosom, g_add=True)
                no_gen_idx = np.nonzero(gen==0)[0]
                gen_to_add = self.MSR_gen_b < self.MSR
                if gen_to_add.any():
                    gen.put(no_gen_idx[gen_to_add], 1)

                    g_idx = np.expand_dims(np.expand_dims(no_gen_idx[gen_to_add],axis=0),axis=2)
                    s_idx = np.expand_dims(np.expand_dims(np.nonzero(sampel)[0],axis=0),axis=0)
                    c_idx = np.expand_dims(np.expand_dims(np.nonzero(kromosom)[0],axis=1),axis=2)

                    self.D[c_idx, g_idx, s_idx] = self.D_asli[c_idx, g_idx, s_idx]
             
                self.hitung_MSR(gen, sampel, kromosom)
            
            # penambahan sampel
                self.hitung_MSR(gen, sampel, kromosom, s_add =True)
                no_sampel = np.nonzero(sampel==0)[0]
                sampel_to_add = self.MSR_sampel_b < self.MSR
                if sampel_to_add.any():
                    sampel.put(no_sampel[sampel_to_add],1)
                    
                    g_idx = np.expand_dims(np.expand_dims(np.nonzero(gen)[0],axis=0),axis=2)
                    s_idx = np.expand_dims(np.expand_dims(no_kondisi[sampel_to_add],axis=0),axis=0)
                    c_idx = np.expand_dims(np.expand_dims(np.nonzero(kromosom)[0],axis=1),axis=2)
                    
                    self.D[c_idx, g_idx, s_idx] = self.D_asli[c_idx, g_idx, s_idx]
             
                self.hitung_MSR(gen, sampel, kromosom)
             
            # penambahan kromosom
                self.hitung_MSR(gen, sampel, kromosom, c_add=True)
                no_kromosom = np.nonzero(kromosom==0)[0]
                kromosom_to_add = self.MSR_kromosom_b < self.MSR
                if kromosom_to_add.any():
                    kromosom.put(no_kromosom[kromosom_to_add],1)
                    
                    g_idx = np.expand_dims(np.expand_dims(np.nonzero(gen)[0],axis=0),axis=2)
                    s_idx = np.expand_dims(np.expand_dims(np.nonzero(sampel)[0],axis=0),axis=0)
                    c_idx = np.expand_dims(np.expand_dims(no_kromosom[kromosom_to_add],axis=1),axis=2)
                    
                    self.D[c_idx, g_idx, s_idx] = self.D_asli[c_idx, g_idx, s_idx]
             
                self.hitung_MSR(gen, sampel, kromosom)

                if not gen_to_add.any() and not sampel_to_add.any() and not kromosom_to_add.any():
                    break

                sys.stdout.write('\r multiple deletion {} - single deletion {} - node addition {}'.format(
                    self.muldel, self.singdel, self.nodeadd
                ))
                sys.stdout.flush()

                # i+=1
                self.nodeadd +=1
            #print("MSR akhir node addition :",self.MSR)
        return gen, sampel, kromosom
    
    
    def mask(self, gen, sampel, kromosom, minval, maxval):
        g = np.expand_dims(np.expand_dims(gen.nonzero()[0],axis=0),axis=2)
        s = np.expand_dims(np.expand_dims(sampel.nonzero()[0],axis=0),axis=0)
        c = np.expand_dims(np.expand_dims(kromosom.nonzero()[0],axis=1),axis=2)
        if (self.mask_mode == 'random'):
            shape = np.count_nonzero(kromosom), np.count_nonzero(gen), np.count_nonzero(sampel)
            mask_val = np.random.uniform(self.minval, self.maxval, shape)
            self.D[c, g, s] = mask_val
        else:
            self.D[c, g, s] = np.nan
    
    def fit(self, delta, lamda, mask_mode, n_triclusters=0):

        awal = time.time()
        
        n_kromosom, n_gen, n_sampel = self.D.shape
        
        self.delta = delta
        self.lamda = lamda
        self.mask_mode = mask_mode
        
        # threshold untuk multiple node deletion
        self.gen_cutoff, self.sampel_cutoff, self.kromosom_cutoff = 50, 50, 50
        # nilai untuk masking
        self.minval, self.maxval = np.nanmin(self.D), np.nanmax(self.D)
        
        hasil_gen = []
        hasil_sampel = []
        hasil_kromosom = []
        
        msr = []

        i = 1
        
        while True:
            self.muldel = 0
            self.singdel =0
            self.nodeadd = 0

            print("Tricluster ",i)
            kromosom = np.ones(n_kromosom, dtype=np.bool)
            gen = np.ones(n_gen, dtype=np.bool)
            sampel = np.ones(n_sampel, dtype=np.bool)
            
            # Multiple Node Deletion
            gen, sampel, kromosom = self.multiple_node_deletion(gen, sampel, kromosom)
            
            # Single Node Deletion
            gen, sampel, kromosom = self.single_node_deletion(gen, sampel, kromosom)
            
            # Node Addition
            gen, sampel, kromosom = self.node_addition(gen, sampel, kromosom)
            
            #print("Jumlah gen akhir", gen.sum())
            

            if (gen.sum()==1) or (sampel.sum()==1) or (kromosom.sum()==1):
                akhir = ((time.time()-awal)/60)
                print("\n Waktu Komputasi : {} menit".format(akhir))
                break
                
            if ((mask_mode == 'nan') and (np.isnan(self.D.all()))):
                break
            
            print("\n--- MSR: ", self.MSR)

            hasil_gen.append(gen)
            hasil_sampel.append(sampel)
            hasil_kromosom.append(kromosom)

            msr.append(self.MSR)

            if (n_triclusters == i):
                break
    
            # mask
            self.mask(gen, sampel, kromosom, self.minval, self.maxval)
            
            i+=1
            
        return hasil_gen, hasil_sampel, hasil_kromosom, msr

"""# Lamda = 1.05

## 1st Simulation (Delta = 0.0466)
"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_1
!mkdir simulasi_1
# %cd simulasi_1

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0466, 1.05, mask_mode='random', n_triclusters=0)

np.savetxt("gen1.txt", g, fmt="%0.f")
np.savetxt("sampel1.txt", s, fmt="%0.f")
np.savetxt("kromosom1.txt", c, fmt="%0.f")
np.savetxt("msr1.txt", msr)

"""## 2nd Simulation (Delta = 0.0566)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_2
!mkdir simulasi_2
# %cd simulasi_2

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0566, 1.05, mask_mode='random', n_triclusters=0)

np.savetxt("gen2.txt", g, fmt="%0.f")
np.savetxt("sampel2.txt", s, fmt="%0.f")
np.savetxt("kromosom2.txt", c, fmt="%0.f")
np.savetxt("msr2.txt", msr)

"""## 3rd Simulation (Delta = 0.0732)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_3
!mkdir simulasi_3
# %cd simulasi_3

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0732, 1.05, mask_mode='random', n_triclusters=0)

np.savetxt("gen3.txt", g, fmt="%0.f")
np.savetxt("sampel3.txt", s, fmt="%0.f")
np.savetxt("kromosom3.txt", c, fmt="%0.f")
np.savetxt("msr3.txt", msr)

"""## 4th Simulation (Delta = 0.0765)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_4
!mkdir simulasi_4
# %cd simulasi_4

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0765, 1.05, mask_mode='random', n_triclusters=0)

np.savetxt("gen4.txt", g, fmt="%0.f")
np.savetxt("sampel4.txt", s, fmt="%0.f")
np.savetxt("kromosom4.txt", c, fmt="%0.f")
np.savetxt("msr4.txt", msr)

"""## 5th Simulation (Delta = 0.0817)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_5
!mkdir simulasi_5
# %cd simulasi_5

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0817, 1.05, mask_mode='random', n_triclusters=0)

np.savetxt("gen5.txt", g, fmt="%0.f")
np.savetxt("sampel5.txt", s, fmt="%0.f")
np.savetxt("kromosom5.txt", c, fmt="%0.f")
np.savetxt("msr5.txt", msr)

"""# Lamda = 1.15

## 6th Simulation (Delta = 0.0466)
"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_6
!mkdir simulasi_6
# %cd simulasi_6

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0466, 1.15, mask_mode='random', n_triclusters=0)

np.savetxt("gen6.txt", g, fmt="%0.f")
np.savetxt("sampel6.txt", s, fmt="%0.f")
np.savetxt("kromosom6.txt", c, fmt="%0.f")
np.savetxt("msr6.txt", msr)

"""## 7th Simulation (Delta = 0.0566)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_7
!mkdir simulasi_7
# %cd simulasi_7

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0566, 1.15, mask_mode='random', n_triclusters=0)

np.savetxt("gen7.txt", g, fmt="%0.f")
np.savetxt("sampel7.txt", s, fmt="%0.f")
np.savetxt("kromosom7.txt", c, fmt="%0.f")
np.savetxt("msr7.txt", msr)

"""## 8th Simulation (Delta = 0.0732)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_8
!mkdir simulasi_8
# %cd simulasi_8

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0732, 1.15, mask_mode='random', n_triclusters=0)

np.savetxt("gen8.txt", g, fmt="%0.f")
np.savetxt("sampel8.txt", s, fmt="%0.f")
np.savetxt("kromosom8.txt", c, fmt="%0.f")
np.savetxt("msr8.txt", msr)

"""## 9th Simulation (Delta = 0.0765)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_9
!mkdir simulasi_9
# %cd simulasi_9

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0765, 1.15, mask_mode='random', n_triclusters=0)

np.savetxt("gen9.txt", g, fmt="%0.f")
np.savetxt("sampel9.txt", s, fmt="%0.f")
np.savetxt("kromosom9.txt", c, fmt="%0.f")
np.savetxt("msr9.txt", msr)

"""## 10th Simulation (Delta = 0.0817)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_10
!mkdir simulasi_10
# %cd simulasi_10

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0817, 1.15, mask_mode='random', n_triclusters=0)

np.savetxt("gen10.txt", g, fmt="%0.f")
np.savetxt("sampel10.txt", s, fmt="%0.f")
np.savetxt("kromosom10.txt", c, fmt="%0.f")
np.savetxt("msr10.txt", msr)

"""# Lamda = 1.25

## 11th Simulation (Delta = 0.0466)
"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_11
!mkdir simulasi_11
# %cd simulasi_11

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0466, 1.25, mask_mode='nan', n_triclusters=0)

np.savetxt("gen11.txt", g, fmt="%0.f")
np.savetxt("sampel11.txt", s, fmt="%0.f")
np.savetxt("kromosom11.txt", c, fmt="%0.f")
np.savetxt("msr11.txt", msr)

"""## 12th Simulation (Delta = 0.0566)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_12
!mkdir simulasi_12
# %cd simulasi_12

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0566, 1.25, mask_mode='random', n_triclusters=0)

np.savetxt("gen12.txt", g, fmt="%0.f")
np.savetxt("sampel12.txt", s, fmt="%0.f")
np.savetxt("kromosom12.txt", c, fmt="%0.f")
np.savetxt("msr12.txt", msr)

"""## 13th Simulation (Delta = 0.0732)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_13
!mkdir simulasi_13
# %cd simulasi_13

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0732, 1.25, mask_mode='random', n_triclusters=0)

np.savetxt("gen13.txt", g, fmt="%0.f")
np.savetxt("sampel13.txt", s, fmt="%0.f")
np.savetxt("kromosom13.txt", c, fmt="%0.f")
np.savetxt("msr13.txt", msr)

"""## 14th Simulation (Delta = 0.0765)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_14
!mkdir simulasi_14
# %cd simulasi_14

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0765, 1.25, mask_mode='random', n_triclusters=0)

np.savetxt("gen14.txt", g, fmt="%0.f")
np.savetxt("sampel14.txt", s, fmt="%0.f")
np.savetxt("kromosom14.txt", c, fmt="%0.f")
np.savetxt("msr14.txt", msr)

"""## 15th Simulation (Delta = 0.0817)"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output

!rm -rf simulasi_15
!mkdir simulasi_15
# %cd simulasi_15

a = DeltaTrimax(arr)
g, s, c, msr = a.fit(0.0817, 1.25, mask_mode='random', n_triclusters=0)

np.savetxt("gen15.txt", g, fmt="%0.f")
np.savetxt("sampel15.txt", s, fmt="%0.f")
np.savetxt("kromosom15.txt", c, fmt="%0.f")
np.savetxt("msr15.txt", msr)

"""# Tricluster Diffusion"""

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/MyDrive/Output
import numpy as np

#simulasi 1
g1 = np.loadtxt('simulasi_1/gen1.txt'); g1 = g1.astype(bool)
s1 = np.loadtxt('simulasi_1/sampel1.txt'); s1 = s1.astype(bool) 
c1 = np.loadtxt('simulasi_1/kromosom1.txt'); c1 = c1.astype(bool)
msr1 = np.loadtxt('simulasi_1/msr1.txt')
 
#simulasi 2
g2 = np.loadtxt('simulasi_2/gen2.txt'); g2 = g2.astype(bool)
s2 = np.loadtxt('simulasi_2/sampel2.txt'); s2 = s2.astype(bool) 
c2 = np.loadtxt('simulasi_2/kromosom2.txt'); c2 = c2.astype(bool)
msr2 = np.loadtxt('simulasi_2/msr2.txt')
 
#simulasi 3
g3 = np.loadtxt('simulasi_3/gen3.txt'); g3 = g3.astype(bool)
s3 = np.loadtxt('simulasi_3/sampel3.txt'); s3 = s3.astype(bool) 
c3 = np.loadtxt('simulasi_3/kromosom3.txt'); c3 = c3.astype(bool)
msr3 = np.loadtxt('simulasi_3/msr3.txt')
 
#simulasi 4
g4 = np.loadtxt('simulasi_4/gen4.txt'); g4 = g4.astype(bool)
s4 = np.loadtxt('simulasi_4/sampel4.txt'); s4 = s4.astype(bool) 
c4 = np.loadtxt('simulasi_4/kromosom4.txt'); c4 = c4.astype(bool)
msr4 = np.loadtxt('simulasi_4/msr4.txt')
 
#simulasi 5
g5 = np.loadtxt('simulasi_5/gen5.txt'); g5 = g5.astype(bool)
s5 = np.loadtxt('simulasi_5/sampel5.txt'); s5 = s5.astype(bool) 
c5 = np.loadtxt('simulasi_5/kromosom5.txt'); c5 = c5.astype(bool)
msr5 = np.loadtxt('simulasi_5/msr5.txt')
 
#simulasi 6
g6 = np.loadtxt('simulasi_6/gen6.txt'); g6 = g6.astype(bool)
s6 = np.loadtxt('simulasi_6/sampel6.txt'); s6 = s6.astype(bool) 
c6 = np.loadtxt('simulasi_6/kromosom6.txt'); c6 = c6.astype(bool)
msr6 = np.loadtxt('simulasi_6/msr6.txt')
 
#simulasi 7
g7 = np.loadtxt('simulasi_7/gen7.txt'); g7 = g7.astype(bool)
s7 = np.loadtxt('simulasi_7/sampel7.txt'); s7 = s7.astype(bool) 
c7 = np.loadtxt('simulasi_7/kromosom7.txt'); c7 = c7.astype(bool)
msr7 = np.loadtxt('simulasi_7/msr7.txt')
 
#simulasi 8
g8 = np.loadtxt('simulasi_8/gen8.txt'); g8 = g8.astype(bool)
s8 = np.loadtxt('simulasi_8/sampel8.txt'); s8 = s8.astype(bool) 
c8 = np.loadtxt('simulasi_8/kromosom8.txt'); c8 = c8.astype(bool)
msr8 = np.loadtxt('simulasi_8/msr8.txt')
 
#simulasi 9
g9 = np.loadtxt('simulasi_9/gen9.txt'); g9 = g9.astype(bool)
s9 = np.loadtxt('simulasi_9/sampel9.txt'); s9 = s9.astype(bool) 
c9 = np.loadtxt('simulasi_9/kromosom9.txt'); c9 = c9.astype(bool)
msr9 = np.loadtxt('simulasi_9/msr9.txt')
 
#simulasi 10
g10 = np.loadtxt('simulasi_10/gen10.txt'); g10 = g10.astype(bool)
s10 = np.loadtxt('simulasi_10/sampel10.txt'); s10 = s10.astype(bool) 
c10 = np.loadtxt('simulasi_10/kromosom10.txt'); c10 = c10.astype(bool)
msr10 = np.loadtxt('simulasi_10/msr10.txt')
 
#simulasi 11
g11 = np.loadtxt('simulasi_11/gen11.txt'); g11 = g11.astype(bool)
s11 = np.loadtxt('simulasi_11/sampel11.txt'); s11 = s11.astype(bool) 
c11 = np.loadtxt('simulasi_11/kromosom11.txt'); c11 = c11.astype(bool)
msr11 = np.loadtxt('simulasi_11/msr11.txt')
 
#simulasi 12
g12 = np.loadtxt('simulasi_12/gen12.txt'); g12 = g12.astype(bool)
s12 = np.loadtxt('simulasi_12/sampel12.txt'); s12 = s12.astype(bool) 
c12 = np.loadtxt('simulasi_12/kromosom12.txt'); c12 = c12.astype(bool)
msr12 = np.loadtxt('simulasi_12/msr12.txt')
 
#simulasi 13
g13 = np.loadtxt('simulasi_13/gen13.txt'); g13 = g13.astype(bool)
s13 = np.loadtxt('simulasi_13/sampel13.txt'); s13 = s13.astype(bool) 
c13 = np.loadtxt('simulasi_13/kromosom13.txt'); c13 = c13.astype(bool)
msr13 = np.loadtxt('simulasi_13/msr13.txt')
 
#simulasi 14
g14 = np.loadtxt('simulasi_14/gen14.txt'); g14 = g14.astype(bool)
s14 = np.loadtxt('simulasi_14/sampel14.txt'); s14 = s14.astype(bool) 
c14 = np.loadtxt('simulasi_14/kromosom14.txt'); c14 = c14.astype(bool)
msr14 = np.loadtxt('simulasi_14/msr14.txt')
 
#simulasi 15
g15 = np.loadtxt('simulasi_15/gen15.txt'); g15 = g15.astype(bool)
s15 = np.loadtxt('simulasi_15/sampel15.txt'); s15 = s15.astype(bool) 
c15 = np.loadtxt('simulasi_15/kromosom15.txt'); c15 = c15.astype(bool)
msr15 = np.loadtxt('simulasi_15/msr15.txt')

# Tricluster Diffusion pada masing-masing delta
 
def TD(m, i, msr):
  x, y, z = m.shape
  v = x*y*z
  td = msr[i]/v
  return td
 
D1 = []
for i in range(len(msr1)):
  m = arr[c1[i]][:,g1[i]][:,:,s1[i]]
  D1.append(TD(m, i, msr1))
D1 = np.array(D1)

D2 = []
for i in range(len(msr2)):
  m = arr[c2[i]][:,g2[i]][:,:,s2[i]]
  D2.append(TD(m, i, msr2))
D2 = np.array(D2)
 
D3 = []
for i in range(len(msr3)):
  m = arr[c3[i]][:,g3[i]][:,:,s3[i]]
  D3.append(TD(m, i, msr3))
D3 = np.array(D3)

D4 = []
for i in range(len(msr4)):
  m = arr[c4[i]][:,g4[i]][:,:,s4[i]]
  D4.append(TD(m, i, msr4))
D4 = np.array(D4)

D5 = []
for i in range(len(msr5)):
  m = arr[c5[i]][:,g5[i]][:,:,s5[i]]
  D5.append(TD(m, i, msr5))
D5 = np.array(D5)

D6 = []
for i in range(len(msr6)):
  m = arr[c6[i]][:,g6[i]][:,:,s6[i]]
  D6.append(TD(m, i, msr6))
D6 = np.array(D6)

D7 = []
for i in range(len(msr7)):
  m = arr[c7[i]][:,g7[i]][:,:,s7[i]]
  D7.append(TD(m,i,msr7))
D7 = np.array(D7)

D8 = []
for i in range(len(msr8)):
  m = arr[c8[i]][:,g8[i]][:,:,s8[i]]
  D8.append(TD(m,i,msr8))
D8 = np.array(D8)

D9 = []
for i in range(len(msr9)):
  m = arr[c9[i]][:,g9[i]][:,:,s9[i]]
  D9.append(TD(m, i, msr9))
D9 = np.array(D9)

D10 = []
for i in range(len(msr10)):
  m = arr[c10[i]][:,g10[i]][:,:,s10[i]]
  D10.append(TD(m, i, msr10))
D10 = np.array(D10)

D11 = []
for i in range(len(msr11)):
  m = arr[c11[i]][:,g11[i]][:,:,s11[i]]
  D11.append(TD(m, i, msr11))
D11 = np.array(D11)

D12 = []
for i in range(len(msr12)):
  m = arr[c12[i]][:,g12[i]][:,:,s12[i]]
  D12.append(TD(m, i, msr12))
D12 = np.array(D12)

D13 = []
for i in range(len(msr13)):
  m = arr[c13[i]][:,g13[i]][:,:,s13[i]]
  D13.append(TD(m, i, msr13))
D13 = np.array(D13)

D14 = []
for i in range(len(msr14)):
  m = arr[c14[i]][:,g14[i]][:,:,s14[i]]
  D14.append(TD(m, i, msr14))
D14 = np.array(D14)

D15 = []
for i in range(len(msr15)):
  m = arr[c15[i]][:,g15[i]][:,:,s15[i]]
  D15.append(TD(m, i, msr15))
D15 = np.array(D15)

print("rata-rata TD pada setiap simulasi \n")
print("mean TD 1 :",np.mean(D1))
print("mean TD 2 :",np.mean(D2))
print("mean TD 3 :",np.mean(D3))
print("mean TD 4 :",np.mean(D4))
print("mean TD 5 :",np.mean(D5))
print("mean TD 6 :",np.mean(D6))
print("mean TD 7 :",np.mean(D7))
print("mean TD 8 :",np.mean(D8))
print("mean TD 9 :",np.mean(D9))
print("mean TD 10 :",np.mean(D10))
print("mean TD 11:",np.mean(D11))
print("mean TD 12 :",np.mean(D12))
print("mean TD 13 :",np.mean(D13))
print("mean TD 14 :",np.mean(D14))
print("mean TD 15 :",np.mean(D15))

"""# The Best Simulation"""

# simulasi terbaik adalah pada simulasi 9
# 10 tricluster dengan TD terkecil pada simulasi 9
for i in range(13):
  x = np.sort(D9)[i]
  y = np.where(D9 == x)
  y = y[0][0]
  yy = y+1
  print("tricluster {} -- TD :{} -- ukuran :{} x {} x {}".format(yy,x,
                                                              np.count_nonzero(g9[y]),
                                                              np.count_nonzero(s9[y]),
                                                              np.count_nonzero(c9[y])))

cluster_kromosom = [0,11,6,2,9,5,10,8,3,1,7,4,12]
for i in cluster_kromosom:
  print('tricluster {} : {}'.format(i,np.nonzero(c9[i])))

for i in range(13):
  x = np.sort(D11)[i]
  y = np.where(D11 == x)
  y = y[0][0]
  yy = y+1
  print("tricluster {} -- TD :{} -- ukuran :{} x {} x {}".format(yy,x,
                                                              np.count_nonzero(g11[y]),
                                                              np.count_nonzero(s11[y]),
                                                              np.count_nonzero(c11[y])))