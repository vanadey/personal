#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET

options = {}


def error(msg,is_fatal = False) :
     sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
     if is_fatal : exit (1)


def vprint(msg):
    if options.verbose:
        print(msg)


def parse_args():
    global options
    # parse arguments
#    usage_text = """Invocation modes:
#%(prog)s --dump-ids
#%(prog)s --read-tipi-data FILE
#"""
#    epilog_text = """Sekcje ankiety:
#    0 : Charakterystyka respondentów
#    1 : Funkcja munduru
#    2 : Ogólne założenia munduru
#    3 : Kompozycja munduru
#    4 : Spódnica mundurowa
#    5 : Sposób noszenia munduru
#    6 : Oznaczenia na mundurze
#    7 : Finanse
#"""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--infile", required=True, action="store", type=str, dest="infile", metavar="FREEPLANE_FILE", help=f"input FreePlane (*.mm) XML file")
    parser.add_argument("--innode", action="store", type=str, dest="innode", metavar="FREEPLANE_NODE_ID", help=f"ID of node to export from FreePlane mind map")
    parser.add_argument("--outfile", required=True, action="store", type=str, dest="outfile", metavar="LOGSEQ_FILE", help=f"output Logseq (*.md) Markdown file")

    parser.add_argument("--verbose", "-v", action="store_true", dest="verbose", default=False)

    options = parser.parse_args()

    return options


def get_md(node: ET.Element) -> str:
    '''parse XML tree and produce Markdown equivalent'''


def get_node_text(node: ET.Element, indent=0) -> str:
    NO_TEXT = "[NO TEXT CONTENT]"
    BOLD_MARK = ""
    ITALIC_MARK = ""

    match node.tag:
        case "font" | "map_styles":
            node.clear()
            return None  # technical non-text nodes with no text beneath them - can be skipped

        case "node":
            node_text = node.get("TEXT", default=NO_TEXT)
            if node_text != NO_TEXT:
                # actual text node
                font_node = node.find("font")
                #vprint('    ' * indent + f"{font_node=}")
                if font_node != None:
                    vprint('    ' * indent + f"{font_node.attrib=}")
                    if font_node.get("BOLD", default="false") == "true":
                        BOLD_MARK = "**"
                    if font_node.get("ITALIC", default="false") == "true":
                        ITALIC_MARK = "*"
                return f"{BOLD_MARK}{ITALIC_MARK}{node_text}{ITALIC_MARK}{BOLD_MARK}"
            else:
                rc_node = node.find("richcontent")
                if rc_node:
                    # rich content node, e.g. image or HTML
                    #node_text = f"[RICH CONTENT NODE, ID={node.get('ID',default='NO_ID')}]"
                    node_text = ""
                    rc_contents = rc_node.findall("html/body/*")  # possibly to handle multiple <p>'s
                    for rc_elem in rc_contents:
                        vprint(f"{rc_elem.tag=}")
                        node_text += ET.tostring(rc_elem, encoding="UTF-8").decode("UTF-8")
                    #return node_text, True
                    node.remove(rc_node)
                    return ' '.join(node_text.split())
                else:
                    return f"[WEIRD NODE WITH NO TEXT, ID={node.get('ID',default='NO_ID')}]", False


        case "hook":
            # directly-pasted images
            # <hook URI="priv_files/png-231222-000848104-16101307044862004068.png" SIZE="0.8108108" NAME="ExternalObject"/>
            pass


        case "icon":
            return f"[ICON: {node.get('BUILTIN', default='custom')}]"

        case _:
            return f"[UNSUPPORTED NODE, ID={node.get('ID',default='NO_ID')}]"  # for the time being


def process_node(node, indent=0):
    node_text = get_node_text(node, indent)  # may delete node's children!
    if node_text != None:
        print('    ' * indent + node_text)
    for child in node.findall('*'):
         process_node(child, indent + 1)


#################################
# Program execution starts here
#################################

if __name__ == '__main__':
    options = parse_args()

    with open(options.infile) as infile:
        xml_string = infile.read()

    # fix unknown entites
    xml_string = xml_string.replace("&nbsp;", "&#160;")
#    # for debugging, if unknown entity is encountered by parser
#    xml_lines = xml_string.splitlines()
#    print(f"{xml_lines[137]=}")

#    mm_parser = ET.XMLParser()
#    import inspect
#    print(f"{mm_parser=}")
#    print(f"{mm_parser.__dir__()=}")
#    print(f"{inspect.getmembers(mm_parser)=}")

    mm_root = ET.fromstring(xml_string)
    vprint(f"{mm_root=}")
    if options.innode:
        mm_node = mm_root.findall(f".//node[@ID='{options.innode}']")[0]
    else:
        mm_node = mm_root
    vprint(f"{mm_node=}")

    process_node(mm_node)
