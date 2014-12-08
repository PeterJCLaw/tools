#!/usr/bin/env python
from __future__ import print_function

import os
import sys


def which(name):
    # Adapted from answer to http://stackoverflow.com/questions/775351/os-path-exists-for-files-in-your-path
    for p in os.environ["PATH"].split(os.pathsep):
        possible_path = os.path.join(p, name)
        if os.path.exists(possible_path):
            return possible_path

    return None

def ensure_callable(*names):
    missing = [name for name in names if which(name) is None]
    if len(missing) == 0:
        return
    end = 'y' if len(missing) is 1 else 'ies'
    print("Missing dependenc{0}: {1}".format(end, ", ".join(missing)))
    sys.exit(1)


def command(args):
    import shutil
    import subprocess
    import tempfile
    import zipfile


    source = args.source.read()

    ensure_callable('pandoc', 'pdflatex')

    pandoc_process = subprocess.Popen(['pandoc', '-f', 'html' if args.html else 'markdown', '-t', 'latex', '-'],
                                      stdin = subprocess.PIPE,
                                      stdout = subprocess.PIPE,
                                      universal_newlines=True)
    pandoc_process.stdin.write(source)
    pandoc_process.stdin.close()
    generated = pandoc_process.stdout.read()
    pandoc_process.wait()

    generated = generated.replace('\section', '\section*').replace('\subsection', '\subsection*')

    prefix = r"""
    \documentclass[a4paper]{article}
    \usepackage[dvinames]{xcolor}
    \usepackage[top=2in,left=1.5in,bottom=2.8in,right=1.25in]{geometry}
    \usepackage{graphicx}
    \usepackage{ctable}
    \usepackage[colorlinks=false,
                pdfborder={0 0 0},]{hyperref}
    \usepackage[absolute]{textpos}
    \usepackage[oldstylenums]{kpfonts}
    \usepackage[T1]{fontenc}
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \parindent0pt
    \setlength{\parskip}{0.8\baselineskip}
    \definecolor{SRblue}{RGB}{13,31,97}
    \definecolor{SRgrey}{RGB}{223,219,215}
    \urlstyle{sf}
    \fancyhead{}
    \fancyfoot{}
    \setlength{\footskip}{3em}
    \renewcommand{\headrulewidth}{0pt}
    \renewcommand{\footrulewidth}{1pt}
    \fancyfoot[C]{\footnotesize\color{SRblue}\sffamily
    Student Robotics, School of Electronics and Computer Science, University of Southampton, SO17 1BJ\\[-0.1\baselineskip]
    \url{info@studentrobotics.org} \textbullet\ \url{http://studentrobotics.org/}\\ \medskip \Huge
    \includegraphics[height=1em]{moto.png}\hfill{}\includegraphics[height=1em]{ecs.png}\hfill{}\includegraphics[height=1em]{bitbox.png} \\ \hfill
    }
    \begin{document}
    \begin{textblock*}{2in}[0.3066,0.39](1.5in,1.33in)
        \includegraphics[width=1.7in]{sr-logo.pdf}
    \end{textblock*}
    \begin{textblock*}{6.375in}(0.65in,1.0in)
        \sffamily
        \begin{flushright}
        \sffamily \Huge \color{SRblue}
        Student Robotics\\ \large
        \smallskip
        School of Electronics and Computer Science\\
        University of Southampton\\
        SO17 1BJ
        \end{flushright}
    \end{textblock*}
    \color{black}
    \vspace*{0.4in}
    """

    suffix = r"""
    \end{document}
    """

    signature_block = ''
    if args.signature:
        signature_elements = args.signature.split(':')
        if len(signature_elements) == 1:
            signature_username = signature_elements[0]
            signature_title = None
        else:
            signature_username, signature_title = signature_elements
        signature_block = '\n'.join([r'\bigskip'] * 5)
        signature_block += '\n{0}\n'.format(signature_username)
        if signature_title:
            signature_block += '\\\\ {0}\n'.format(signature_title)

    total = '\n'.join((prefix, generated, signature_block, suffix))

    if args.latex:
        args.output.write(total)
        sys.exit(0)

    temp_dir = tempfile.mkdtemp('srdoc')

    main_file = os.path.join(temp_dir, 'main.tex')
    with open(main_file, 'w') as f:
        f.write(total)

    zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'latex-assets.zip')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in ('ecs.png', 'moto.png', 'bitbox.png', 'sr-logo.pdf'):
            zf.extract(name, temp_dir)

    pdflatex_proc = subprocess.Popen(['pdflatex', '-interaction=nonstopmode', 'main.tex'],
                                     cwd = temp_dir,
                                     stderr = subprocess.PIPE,
                                     stdout = subprocess.PIPE,
                                     universal_newlines=True)

    while pdflatex_proc.returncode is None:
        (out, err) = pdflatex_proc.communicate()
        errors = [line for line in out.split(os.linesep) if len(line) > 0 and line[0] == '!']
        if len(errors) > 0:
            print(os.linesep.join(errors))

    output_file = os.path.join(temp_dir, 'main.pdf')
    success = pdflatex_proc.returncode == 0 and os.path.exists(output_file)
    if success:
        with open(output_file, 'rb') as f:
            args.output.write(f.read())

    shutil.rmtree(temp_dir)

    if not success:
        print('Error: pdflatex failed to produce output')
        sys.exit(1)


def add_subparser(subparser):
    import argparse


    parser = subparser.add_parser('document', description="Generate formatted documents.")
    parser.add_argument("source", metavar="FILE", type=argparse.FileType('r'),
                        help="Source markdown file")
    parser.add_argument("-o","--output", dest="output",
                        metavar="FILE", type=argparse.FileType('wb'),
                        help="Output file", required=True)
    parser.add_argument("-l", action="store_true", dest="latex",
                        help="Emit LaTeX source rather than PDF")
    parser.add_argument("-s", dest="signature", type=str,
                        help="Add a signature space")
    parser.add_argument("-H", action="store_true", dest="html",
                        help="Take HTML rather than markdown")
    parser.set_defaults(func=command)
