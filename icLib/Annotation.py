'''Annotation
The Annotation class creates an object describing the link between
objects (in the form of AnnotatedObject objects) and ontological terms.
This contains not only the link, but information describing the link
including evidence codes, qualifiers (if present), etc.

Author: Patrick Osterhaus   s-osterh
'''
import AnnotatedObject

class Annotation:

    def __init__(self,ont,details):
        #note the reliance of details in this section
        #dot variables are used for sake of later brevity
        #however more information can be reached within self.details
        #e.g., self.details["EvidenceCode"] and self.evCode are equivalent
        self.annObj=AnnotatedObject.AnnotatedObject.getAnnotatedObj(details["annID"])
        self.ontTerm=ont.getTerm(details["termID"])
        self.evCode=details["EvidenceCode"]
        self.qualifier=details["Qualifier"]
        self.details=details
