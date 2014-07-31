'''simmerEngine
This is the search engine to which the three different implementations feed
requests. This is the consolidated search engine and will hold the bulk, if not
all, computation instead of the three drivers.

Author: Patrick Osterhaus   s-osterh
'''
import sys
import os
import ConfigParser
import json

from icLib import Ontology
from icLib import DAG
from icLib import ConfigManager
from icLib import OntologyManager
from icLib import AnnotationManager
from icLib import CompiledAnnotationSet
from icLib import AnnotatedObject
from icLib import Logger
from icLib import Labeler

#NOTE:It is much better in REPL to use requestSubmissionPC so that each query
#does not require a new Pre-Computation I step
def requestSubmissionPC(annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,logger,labeler,ontman,annman,form="plaintext"):
    #annSetChoice   =   string specifying desired AnnSet (e.g., 'geneGO' or 'genotypeMP')
    #evCodesChoice  =   string specifying desired evCodes to remove (e.g., 'ND,ISO,ISS')
    if searchType not in ["object","list"]:print "Problem with parameter 3."
    if methodChoice not in ["resnikBMA","jaccardExt","gicExt"]:print "Problem with parameter 6."
    if not isinstance(length,int):print "Problem with parameter 7."
    if annSetChoice not in annman.annotationSets:print "Problem with parameter 1."
    annset=annman.annotationSets[annSetChoice]
    evCodes=list(set(evCodesChoice.split(",")))
    cas=CompiledAnnotationSet.CompiledAnnotationSet.getCAS(annset,evCodes,ontman)
    if searchType=="object":query=AnnotatedObject.AnnotatedObject.getAnnotatedObj(searchInput)
    if searchType=="list":query=[cas.annset.ontology.getTerm(x)for x in searchInput.replace(" ,",",").replace(" ",",").split(",")]
    print "Running Semantic Similarity Measure..."
    if methodChoice=="resnikBMA":ret=cas.resnikBMA(searchType,query,namespaceChoice,length)
    if methodChoice=="jaccardExt":ret=cas.jaccardExt(searchType,query,namespaceChoice,length)
    if methodChoice=="gicExt":ret=cas.gicExt(searchType,query,namespaceChoice,length)
    if form=="plaintext":return plaintextFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    elif form=="json":return jsonFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    elif form=="html":return htmlFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    else:return ret

def requestSubmissionRaw(annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,form="plaintext"):
    #annSetChoice   =   string specifying desired AnnSet (e.g., 'geneGO' or 'genotypeMP')
    #evCodesChoice  =   string specifying desired evCodes to remove (e.g., 'ND,ISO,ISS')
    if searchType not in ["object","list"]:print "Problem with parameter 3."
    if methodChoice not in ["resnikBMA","jaccardExt","gicExt"]:print "Problem with parameter 6."
    if not isinstance(length,int):print "Problem with parameter 7."
    print "Pre-Computation I..."
    logger=Logger.Logger()
    cm=ConfigManager.ConfigManager(setConfigOptions)
    simmercon=cm.readConfig()
    #readConfig() returns a SimmerConfigParser so simmercon is a SimmerConfigParser
    labeler=Labeler.Labeler(simmercon)
    ontman=OntologyManager.OntologyManager(simmercon)
    annman=AnnotationManager.AnnotationManager(simmercon,ontman)
    if annSetChoice not in annman.annotationSets:print "Problem with parameter 1."

    annset=annman.annotationSets[annSetChoice]
    evCodes=list(set(evCodesChoice.split(",")))
    cas=CompiledAnnotationSet.CompiledAnnotationSet.getCAS(annset,evCodes,ontman)
    if searchType=="object":query=AnnotatedObject.AnnotatedObject.getAnnotatedObj(searchInput)
    if searchType=="list":query=[cas.annset.ontology.getTerm(x)for x in searchInput.replace(" ,",",").replace(" ",",").split(",")]
    print "Running Semantic Similarity Measure..."
    if methodChoice=="resnikBMA":ret=cas.resnikBMA(searchType,query,namespaceChoice,length)
    if methodChoice=="jaccardExt":ret=cas.jaccardExt(searchType,query,namespaceChoice,length)
    if methodChoice=="gicExt":ret=cas.gicExt(searchType,query,namespaceChoice,length)
    if form=="plaintext":return plaintextFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    elif form=="json":return jsonFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    elif form=="html":return htmlFormatter(ret,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler)
    else:return ret

def plaintextFormatter(dic,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler):
    if namespaceChoice=="MPheno.ontology":labelType="genotype"
    else:labelType="gene"
    header="".join((namespaceChoice,":Top",str(length),methodChoice,"results for ",searchInput))
    body=""
    for x in dic:body=body+"".join(("\n",labeler.get(labelType,x[0].id),"\t\t",str(x[1])))
    tail=" ".join([x[0].id for x in dic])
    return "\n".join((header,body,tail))

def jsonFormatter(dic,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler):
    if namespaceChoice=="MPheno.ontology":labelType="genotype"
    else:labelType="gene"
    ret={"params":{"annSetChoice":annSetChoice,
                    "evCodesChoice":evCodesChoice,
                    "searchType":searchType,
                    "searchInput":searchInput,
                    "namespaceChoice":namespaceChoice,
                    "methodChoice":methodChoice,
                    "length":length},
          "results":[(labeler.get(labelType,x[0].id).replace("\t"," "),x[1]) for x in dic]}
    return json.dumps(ret)

def htmlFormatter(dic,annSetChoice,evCodesChoice,searchType,searchInput,namespaceChoice,methodChoice,length,labeler):
    if namespaceChoice=="MPheno.ontology":labelType="genotype"
    else:labelType="gene"
    ret='<table border="1"><thead><th>Result</th><th>Score</th></thead><tbody>'
    for x in dic:
        ret=ret+"<tr><td>"+labeler.get(labelType,x[0].id).replace("\t"," ")+"</td><td>"+str(x[1])+"</td></tr>"
    ret=ret+"</tbody></table>"
    return ret

def setConfigOptions(op):
    op.add_option("-l", "--length", metavar="NUM", dest="n", type="int", help="A number.")
