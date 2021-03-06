'''CompiledAnnotationSet
This is a file containing the CompiledAnnotationSet class which defines a
CompiledAnnotationSet object. This object contains an AnnotationSet object
after filtering out specified evidence codes. Information is then computed
and stored within this object in the form of dictionaries describing
to which terms an object is annotated, to which objects terms are annotated,
and the information content value of each term. This information is used later
by the semantic similarity measure methods, also defined in this class.

Author: Patrick Osterhaus   s-osterh
'''
import math
import time

import AnnotatedObject
import Logger
import Ontology

class CompiledAnnotationSet:
    knownCAS={}

    @classmethod
    def getCAS(cls,AnnSet,evCodes,ontman):
        if (AnnSet,frozenset(evCodes.split(",")),ontman) in cls.knownCAS:
            return cls.knownCAS[(AnnSet,frozenset(evCodes.split(",")),ontman)]
        else:
            start=time.time()
            print "Pre-Computation II (Building a CompiledAnnotationSet)..."
            newCAS=CompiledAnnotationSet(AnnSet,evCodes,ontman)
            print time.time()-start
            return newCAS
    
    def __init__(self,AnnSet,evCodes,ontman):
        self.knownCAS[(AnnSet,frozenset(evCodes.split(",")),ontman)]=self
        self.ontman=ontman
        self.evCodes=evCodes#might not be used anywhere else; but saved as a remnant to help debugging
        self.annset=AnnSet.evidenceFilter(evCodes)
        self.logger=Logger.Logger()
        self.Compute_obj2term()
        self.Compute_term2obj()
        self.Compute_term2IC()
        #self.Compute_pair2MICA()

    def Compute_term2obj(self):
        self.term2obj={}
        for x in self.annset.getAnnotatedTerms():
                temp=set([])
                for y in self.annset.ontology.closure[x]:
                    if not isinstance(self.annset.getAnnotsByTerm,list):
                        for z in self.annset.getAnnotsByTerm(y):
                                temp.add(z.annObj)
                    else:
                        continue
                self.term2obj[x]=temp

    def Compute_obj2term(self):
        self.obj2term={}
        for x in self.annset.getAnnotatedObjects():
            temp=[]
            for y in self.annset.getAnnotsByObject(x):
                temp.append(y.ontTerm)
            self.obj2term.setdefault(x,set([])).update(temp)

    def Compute_term2IC(self):
        self.term2IC={}
        for x in self.term2obj:
            if len(self.term2obj[x])==0:
                self.term2IC[x]=None
            else:
                self.term2IC[x]=math.log(len(self.term2obj[self.annset.ontology.getRoots(x.namespace)[0]])/float(len(self.term2obj[x])))
                
    def Compute_pair2MICA(self):
        self.pair2MICA={}
        for x in self.term2IC:
            for y in self.term2IC:
                if self.pair2MICA.has_key((y,x)):
                    continue
                else:                    
                    self.pair2MICA.update[(x,y)]=self.getMICAscore(x,y)
                    
    def maxIC(self,lst):
        return max([self.term2IC.get(x,0)for x in lst])if len(lst)>0 else 0.0

    def getMICAscore(self,termA,termB):
        #term to term comparison
        self.MICAcount+=1
        return self.maxIC(self.annset.ontology.reverseClosure[termA]&self.annset.ontology.reverseClosure[termB])

    def rowMICA(self,termA,listB):
        #term to list comparison
        return max([self.getMICAscore(termA,y)for y in listB])

    def listCompare(self,listA,listB):
        #list to list comparison
        lst=[self.rowMICA(y,listB)for y in listA]
        return float(sum(lst))/len(lst)

    def resnikBMA(self,qType,rawQuery,namespace,length):
        #BMA approach; obj to list of objs comparison
        #eventually normalize for the maximum (identity) score to equal 1
        start=time.time()
        self.MICAcount=0
        query=[]
        resultsList=[]
        if qType=="object":query=self.obj2term[rawQuery]
        else:query=rawQuery
        query=[x for x in query if x.namespace==namespace]
        if len(query)==0:
            for x in self.annset.getAnnotatedObjects():resultsList.append((x,0.0))
        for x in self.annset.getAnnotatedObjects():
            res=[z for z in self.obj2term[x] if z.namespace==namespace]
            if len(res)==0:resultsList.append((x,0.0))
            else:resultsList.append((x,self.listCompare(query,res)))
        self.logger.debug("".join(("\nFinished!\tresnikBMA\t",str(self.MICAcount)," MICA calculations\nactual runtime:\t\t",str(time.time()-start)," seconds\n")))
        return sorted(resultsList,key=lambda x:x[1],reverse=True)[0:length]

    def jaccardExt(self,qType,que,namespace,length):
        start=time.time()
        resultsDict={}
        returnDict={}
        resultsList=[]
        query=set([])
        if qType=="object":
            for x in self.obj2term[que]:
                if x.namespace==namespace:
                    query|=self.annset.ontology.reverseClosure[x]
        else:
            for x in que:
                if x.namespace==namespace:
                    query|=self.annset.ontology.reverseClosure[x]
        for x in self.annset.getAnnotatedObjects():
            test=set([])
            for y in self.obj2term[x]:
                if y.namespace==namespace:
                    test|=self.annset.ontology.reverseClosure[y]
            if len(query|test)==0:
                resultsList.append((x,0.0))
            else:
                resultsList.append((x,float(len(query&test))/len(query|test)))
        self.logger.debug("".join(("\nFinished!\tjaccardExt\t",str(time.time()-start)," seconds\n")))
        return sorted(resultsList,key=lambda x:x[1],reverse=True)[0:length]

    def gicExt(self,qType,que,namespace,length):
        start=time.time()
        resultsList=[]
        query=set([])
        if qType=="object":
            for x in self.obj2term[que]:
                if x.namespace==namespace:
                    query|=self.annset.ontology.reverseClosure[x]
        else:
            for x in que:
                if x.namespace==namespace:
                    query|=self.annset.ontology.reverseClosure[x]
        for x in self.annset.getAnnotatedObjects():
            test=set([])
            for y in self.obj2term[x]:
                if y.namespace==namespace:
                    test|=self.annset.ontology.reverseClosure[y]
            if sum([self.term2IC.get(d,0)for d in query|test])==0:
                resultsList.append((x,0.0))
            else:
                resultsList.append((x,sum([self.term2IC.get(z,0)for z in query&test])/sum([self.term2IC.get(d,0)for d in query|test])))
        self.logger.debug("".join(("\nFinished!\tgicExt\t",str(time.time()-start)," seconds\n")))
        return sorted(resultsList,key=lambda x:x[1],reverse=True)[0:length]
