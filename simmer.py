import os
import ConfigParser
import optparse

from icLib import Ontology
from icLib import DAG
from icLib import Annotation_Manager
from icLib import Ontology_Manager

def main():
    options=optionParser()
    direc=os.path.dirname(__file__)
    cp=ConfigParser.RawConfigParser()
    cp.read(os.path.join(direc,options.configFile))
    datadir=os.path.join(direc,cp.get('DEFAULT','datadir'))
    print "data directory:\t",datadir
    ontdir=os.path.join(datadir,cp.get('DEFAULT','ontdir'))
    print "ont directory:\t",ontdir
    anndir=os.path.join(datadir,cp.get('DEFAULT','anndir'))
    print "ann directory:\t",anndir,"\n"
    ontfiledescripts=[]
    annfiledescripts=[]
    for s in cp.sections():
        if "Ontology" in s:
            ontfiledescripts.append([cp.get(s,'onttype'),os.path.join(ontdir,cp.get(s,'filename'))])
        if "AnnotData" in s:
            annfiledescripts.append([cp.get(s,'anntype'),os.path.join(anndir,cp.get(s,'filename')),cp.get(s,'obtype')])
    print ontfiledescripts
    print annfiledescripts,"\n"
    ontman=Ontology_Manager.Ontology_Manager()
    ontologies=ontman.ontsload(ontfiledescripts)
    for x in ontologies:
        print x.getNamespaces()
    print "\n"
    annman=Annotation_Manager.Annotation_Manager()
    annotations=annman.annsload(annfiledescripts)
    for x in annotations:
        print x[0:3]
    print "\n"

    

def optionParser():
    parser=optparse.OptionParser()
    #parser.add_option("-o","--ontology",dest="ontoChoice",default="0",help="Which ontology? 0 for GO, anything else for MP. (default=%default)")
    #parser.add_option("-e","--evidence",dest="evidenceCodeStrings",default="None",help="What evidence codes would you like to remove? (Separate evidence codes by commas. Spaces can be used. Specify 'None' to not remove evidence codes. See http://www.geneontology.org/GO.evidence.shtml)(default=%default)")
    #parser.add_option("-f","--file",dest="fileName",default="data\gene_association.mgi",help="Which gene or phenotype file would you like to use as input?(default=%default)")
    #parser.add_option("-d","--diseasefile",dest="diseaseFile",default="data\Geno_11_OMIM.txt",help="For use with MP terms. Specify which file, containing OMIM data, is desired for input.(default=%default)")
    #parser.add_option("-l","--length",type="int",dest="length",default=25,help="Select how many results (matches) are desired. Values will be rounded down to nearest integer of lesser value.(default=%default)")

    #above commented options will probably have their place in final iteration

    parser.add_option("-c","--config",dest="configFile",default='config.cfg',help="Specify config file location. (default=%default)")
    (options,args)=parser.parse_args()
    return options

main()
