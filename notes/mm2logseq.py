#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import urllib.parse as UP
import os, os.path, shutil
import sys

import random, string  # for generating random strings...

MAX_LEVELS = 20
BACKSLASH_PLACEHOLDER = "Logseq_backslash_placeholder666"
NAMESPACE_PLACEHOLDER = "namespace_placeholder666"

options = {}

icon_map = {
        "aws_clock" : '⏰',
        "aws_gears" : '⚙️',
        "aws_support" : '💁',
        "back" : '⬅️',
        "bee" : '🐝',
        "broken-line" : '🔋',
        "button_cancel" : '✖️',
        "button_ok" : '✔️',
        "calendar" : '📅',
        "checked" : '☑️',
        "clanbomber" : '💣',
        "clock" : '📆',
        "clock2" : '📆',
        "closed" : '⛔',
        "edit" : '📝',
        "emoji-1F480" : '💀',
        "flag-blue" : '🏴',
        "forward" : '➡️',
        "full-0" : '0️⃣',
        "full-1" : '1️⃣',
        "full-2" : '2️⃣',
        "full-3" : '3️⃣',
        "full-4" : '4️⃣',
        "full-5" : '5️⃣',
        "full-6" : '6️⃣',
        "go" : '🆗',
        "help" : '❓',
        "hourglass" : '⌛',
        "idea" : '💡',
        "info" : 'ℹ️',
        "ksmiletris" : '😃',
        "launch" : '🚀',
        "list" : '📋',
        "Mail" : '✉️',
        "male1" : '👨',
        "messagebox_warning" : '⚠️',
        "password" : '🔑',
        "pencil" : '🖉',
        "stop" : '🛑',
        "very_negative" : '➖',
        "very_positive" : '➕',
        "yes" : '❗',
}
icon_mapping = { k : f"@@html: <span style='display:inline; font-size:28pt'>{v}</span>@@ " for k, v in icon_map.items() }

# this is not actually used, but here for documentation purposes
icon_ignore = frozenset([
    "0%",
    "25%",
    "50%",
    "75%",
    "males",
    "family",
    "icon_not_found",
])



def error(msg,is_fatal = False) :
     sys.stderr.write("{0:s} error: {1:s}\n".format("Fatal" if is_fatal else "Non-fatal",msg))
     if is_fatal : exit (1)



def vprint(arg0, arg1=None):
    """ stupid Python does not support function overloading, so let's hack some... """
    if arg1 == None:  # do not want to check for trueness, as e.g. empty string is False
        # vprint(msg):
        sys.stderr.write(arg0 + '\n')
    else:
        # vprint(lvl, msg):
        if options.verbose >= arg0:
            sys.stderr.write(arg1 + '\n')
    sys.stderr.flush()


"""
def vprint(msg):
    sys.stderr.write(msg + '\n')



def vprint(lvl, msg):
    if options.verbose >= lvl:
        sys.stderr.write(msg + '\n')
"""



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
    parser.add_argument("--infile", required=True, action="store", dest="infile", metavar="FREEPLANE_FILE", help="input FreePlane (*.mm) XML file")
    parser.add_argument("--innode", action="store", dest="innode", metavar="FREEPLANE_NODE_ID", help="ID of node to export from FreePlane mind map")
    parser.add_argument("--outfile", required=True, action="store", dest="outfile", metavar="LOGSEQ_FILE", help="output Logseq (*.md) Markdown file")

    #parser.add_argument("--namespace", action="store", dest="namespace", metavar="NAMESPACE", help=f"Logseq namespace to create the pages hierarchy in")
    break_map = parser.add_argument_group("subpages", "control breaking mindmap into subpages")
    break_map.add_argument("--break-at-images", "-b", action="store_true", dest="break_pages_at_images", default=False,
                           help="break page (create linked subpages) at nodes containing HTML images ('icons' in this use case)")
    break_map.add_argument("--nobreak", "-n", action="extend", dest="no_break_nodes", nargs="+",
                           help="do not break at specified nodes or below them; does nothing if --break-at-images | -b was not specified")
    break_map.add_argument("--forcebreak", "-f", action="extend", dest="force_break_nodes", nargs="+", help="force break at specified nodes")
    break_map.add_argument("--break-at-root", action="store_true", dest="break_at_root", default=False, help="always break at direct children of root node")
    break_map.add_argument("--use-namespace", action="store", dest="use_namespace", nargs='?', default=NAMESPACE_PLACEHOLDER, metavar="NAMESPACE",
                           help="create subpages under Logseq namespace NAMESPACE, or named after LOGSEQ_FILE if not specified explicitly")

    technical = parser.add_argument_group("technical options")
    technical.add_argument("--verbose", "-v", action="count", dest="verbose", default=0)
    technical.add_argument("--printresult", "-p", action="store_true", default=False, dest="print_result", help="print resulting Markdown also to stdout")

    options = parser.parse_args()

    # sanity checks
    if options.outfile.lower().endswith(".md"):
        options.outfile = options.outfile[:-3]

    return options



def is_image(uri):
    for ext in [".png", ".jpg", ".jpeg", ".gif"]:
        if uri.lower().endswith(ext):
            return True
    return False



def migrate_img(img_uri, imgdir, srcdir):
    if is_image(img_uri):
        if not os.path.isdir(imgdir):
            os.mkdir(imgdir)
        img_filename = os.path.basename(img_uri)
        src_img = os.path.join(srcdir, img_uri)
        if os.path.exists(src_img):
            try:
                shutil.copy2(src_img, imgdir)
            except:
                sys.stderr.write(f"Cannot copy image file {src_img} to directory {imgdir}\n")
    else:
        sys.stderr.write(f"File {img_uri} is not an image, skipping\n")
    return os.path.join(imgdir, img_filename)



def shall_split_page(node: ET.Element):
    """ determine whether we should split off a subpage at the given node
        the criterion is simple: we break at nodes including images included via HTML """
    if not options.break_pages_at_images:
        return False

    if (rc_node := node.find("richcontent")) == None:
        return False

    if len(rc_node.findall(".//img")) == 0:
        return False

    return True



def sanitize_fs_entry(name: str) -> str:
    # replace fs-unsafe chars: slash, colon...
    xldict = { ':' : ' - ',
               '?' : '',
               '/' : '_',
               '@' : ' at ',
               '\\' : '_' }
    for f,t in xldict.items():
        name = name.replace(f, t)

    # replace weird whitespace with regular space
    name = " ".join(name.split())

    return name


def split_node(node: ET.Element, outdir, imgdir, srcdir, namespace):
    vprint(2, f"[debug] splitting on node with ID={node.get('ID',default='NO_ID')}")
    rc_node = node.find("richcontent")

    # first, extract submap title

    # get actual text content
    if (node_text := node.get("TEXT")) != None:
        submap_name = node_text
    else:
        # pure richcontent node

        # may contain text in <p>
        tc_ = [t.strip().replace('/','_') for t in rc_node.itertext() if t.strip()]
        tc = " ".join(tc_)
        if tc != "":
            submap_name = tc
        else:
            # no text - need to extract name from image file name
            ps = rc_node.findall(".//img")
            if len(ps) > 1:
                submap_name = ''.join(random.choices(string.ascii_lowercase, k=8))
                sys.stderr.write(f"Cannot determine subpage title - no explicit text and multiple images: ID={node.get('ID',default='NO_ID')}; using random name {submap_name}")
            img_name = os.path.basename(ps[0].get("src"))
            vprint(f"img recognized in HTML! {img_name}")
            submap_name = os.path.splitext(img_name)[0]

    submap_name = sanitize_fs_entry(submap_name)
    vprint(f"Splitting off subpage '{submap_name}' at node of ID={node.get('ID',default='NO_ID')}")

    process_map(node, outdir, submap_name, imgdir, srcdir, namespace)

    # return link to created subpage
    if namespace:
        return f"[[{namespace}]]/[[{submap_name}]]"
    else:
        return f"[[{submap_name}]]"



def get_md(node: ET.Element, indent, imgdir, srcdir) -> str:
    NO_TEXT = "[NO TEXT CONTENT]"
    FORMAT_MARK = ""
    HEADER_MARK = ""
    ICON = ""

    # get actual text content
    if (node_text := node.get("TEXT")) != None:
        node_text = node_text.replace(BACKSLASH_PLACEHOLDER, "\\\\")
        # plain text node
        font_node = node.find("font")
        if '\n' in node_text:
            node_text_lines = node_text.split('\n')
            node_text_lines = [l.replace('#', "\\#") for l in node_text_lines]  # '#' is Markdown's header marker, we need to escape it
            #node_text_lines = [l.replace(BACKSLASH_PLACEHOLDER, "&#x5c;") for l in node_text_lines]  # Python's XML parser sucks for handling backslashes
            node_text_lines_out = [node_text_lines[0]]
            for l in node_text_lines[1:]:
                if l.startswith("- "):
                    l = "– " + l[2:]  # '-' is Markdown's indent marker, we replace it with en-dash
                node_text_lines_out.append(l)
            node_text = ('\n' + '\t' * indent + "  ").join(node_text_lines_out)

        #vprint('    ' * indent + f"{font_node=}")
        if font_node != None:
            if font_node.get("BOLD", default="false") == "true":
                FORMAT_MARK += "**"
            if font_node.get("ITALIC", default="false") == "true":
                FORMAT_MARK += "*"

        # styled?
        style_attr = node.get("LOCALIZED_STYLE_REF", default=None)
        if style_attr != None:
            if style_attr.startswith("AutomaticLayout.level,"):
                level = style_attr[22:]
                if level.isdecimal():
                    HEADER_MARK = '#' * int(level) + ' '

    else:

        # rich content node
        if (rc_node := node.find("richcontent")):
            # rich content node, e.g. image or HTML
            # now look for images...
            for img_node in rc_node.findall(".//img"):
                img_uri = img_node.get("src")
                vprint(f"img uri recognized in HTML! {img_uri}")
                new_uri = migrate_img(img_uri, imgdir, srcdir)
                img_node.set("src", new_uri)
            # now extract the actual contents
            # this way we will extract already-updated image URIs
            node_text = ""
            rc_contents = rc_node.findall("html/body/*")  # possibly to handle multiple <p>'s
            for rc_elem in rc_contents:
                node_text += ET.tostring(rc_elem, encoding="UTF-8").decode("UTF-8")
            #node.remove(rc_node)
            node_text = ' '.join(node_text.split())
        else:
            node_text = f"[WEIRD <{node.tag}> NODE WITH NO TEXT, ID={node.get('ID',default='NO_ID')}]"

    # handle possible link
    if (link_url := node.get("LINK")) != None:
        node_text += f" ([link]({link_url}))"

    # handle possible icon
    if (icon_node := node.find("icon")) != None:
        if (mm_icon := icon_node.get("BUILTIN")) != None:
            #translate icon to emoji
            ICON = icon_mapping.get(mm_icon, "")

    # handle images included via <hook>
    if (hook_node := node.find("hook")) != None:
        hook_uri = hook_node.get("URI")
        vprint(f"hook uri recognized! {hook_uri}")
        if hook_uri != None:  # <hook> nodes may also specify styles etc.
            new_uri = migrate_img(hook_uri, imgdir, srcdir)
            node_text = f"![{node_text}]({new_uri})"

    return f"{HEADER_MARK}{ICON}{FORMAT_MARK}{node_text}{FORMAT_MARK}"



def process_node(node, indent, outdir, outfile, imgdir, srcdir, namespace, prevent_split = False, force_split=False):
    # if `option.break_at_root`, `force_split` needs to be True for SECOND level of nodes
    global options

    node_id = node.get('ID',default='NO_ID')
    vprint(2, f"[debug] processing node with ID={node_id}, {indent=}")

    if indent > MAX_LEVELS: 
        sys.stderr.write(f"Maximum recursion level of {MAX_LEVELS} exceeded, exiting.")
        sys.exit(1)

    out = ""

    if options.no_break_nodes and node_id in options.no_break_nodes:
        prevent_split = True  # this will be passed to children

    # do we split in this node? (i.e. shall this node become root of a submap?)
    if prevent_split:
        splitting_here = False

    if options.force_break_nodes and node_id in options.force_break_nodes:
        splitting_here = True

    elif force_split:
        splitting_here = True
    elif indent > 0:
        splitting_here = shall_split_page(node)
    else:
        splitting_here = False

    # indent==0 means map root
    node_text = get_md(node, indent, imgdir, srcdir)  # may modify node if we are splitting there
    if indent == 0:
        # map root node
        if "<img" not in node_text:
            # plaintext node
            out = f"# {node_text}\n"
        else:
            # rich content node
            out = f"{node_text}\n\n***\n\n"

    else:
        if splitting_here:
            node_text = split_node(node, outdir, imgdir, srcdir, namespace)

        if node_text != None:
            INDENT = '\t' * indent
            out = f"{INDENT}- {node_text}\n"

    if indent == 0 and options.break_at_root:
        force_split = True
        options.break_at_root = False

    if not splitting_here:
        for child in node.findall('node'):
             out += process_node(child, indent+1, outdir, outfile, imgdir, srcdir, namespace, prevent_split, force_split)

    if out == "":
        sys.stderr.write(f"Internal error: no text for node with ID={node.get('ID',default='NO_ID')}")

    return out



def process_map(root, outdir, outfile, imgdir, srcdir, namespace):
    vprint("[debug] process_map() called")

    outfile_actual = outfile + ".md"
    if namespace:
        outfile_actual = namespace + "___" + outfile_actual
    else:
        if options.use_namespace:
            if options.use_namespace != NAMESPACE_PLACEHOLDER:
                namespace = options.use_namespace
            else:
                namespace = outfile  # for child maps

    output = process_node(root, 0, outdir, outfile, imgdir, srcdir, namespace)

    with open(os.path.join(outdir, outfile_actual), 'w') as of:
        vprint(f"Writing to file {outdir+'/'+outfile_actual}")
        of.write(output)

    if options.print_result:
        print(output)



#################################
# Program execution starts here
#################################

if __name__ == '__main__':
    options = parse_args()

    with open(options.infile) as infile:
        xml_string = infile.read()

    # fix unknown entites
    xml_string = xml_string.replace("&nbsp;", "&#160;")
    xml_string = xml_string.replace("\\", BACKSLASH_PLACEHOLDER)
#    # for debugging, if unknown entity is encountered by parser
#    xml_lines = xml_string.splitlines()
#    print(f"{xml_lines[137]=}")

    mm_root = ET.fromstring(xml_string)
    vprint(f"{mm_root=}")
    if options.innode:
        mm_node = mm_root.findall(f".//node[@ID='{options.innode}']")[0]
    else:
        mm_node = mm_root.find("node")  # the root of whole map is <map>
    vprint(f"{mm_node=}")

    # original mindmap directory
    srcdir = os.path.dirname(os.path.realpath(options.infile))

    # output locations
    options.outfile = os.path.realpath(options.outfile)
    outdir = os.path.dirname(options.outfile)
    outfile = os.path.basename(options.outfile)

    # subdirectory to store possible images
    imgdir = options.outfile  # this will be different from actual outfile for submaps

    process_map(mm_node, outdir, outfile, imgdir, srcdir, namespace=None)
