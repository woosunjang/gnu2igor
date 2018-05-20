#!/usr/local/bin/python
import math
import numpy as np
import re
import argparse

class gnu2igor(object):
    def __init__(self, outfile):
        self.kpts = None
        self.ktraj = None
        self.band = None
        self.guideticks = None
        self.input_name = input("Please input the name of system  :  ")

        if outfile is None:
            self.outfile = "band.itx"
        else:
            self.outfile = outfile
        return

    def gnuband_parser(self, gnu_xaxis, gnu_data, gnu_plotdata):
        band = []
        kpts = []
        ktraj = []

        if gnu_xaxis is not None:
            with open(gnu_xaxis, 'r') as xaxis:
                kpt_raw = xaxis.readlines()
                num_kpt = int(kpt_raw[0].split()[0])

                for x in kpt_raw[1:]:
                    kpts.append(x.split())

            self.kpts = np.array(kpts, dtype='d')

        with open(gnu_data, 'r') as yaxis:
            lines = yaxis.readlines()

            if self.kpts is None:
                for x in enumerate(lines):
                    if len(re.findall(r"[\w.\n]+", x[1])) == 1:
                        num_kpt = x[0]
                        break

            num_bands = int(len(lines) / (num_kpt + 1))
            nextline = int(num_kpt) + 1

            # for i in range(num_bands):
            #     tmp = []
            #     for j in range(num_bands):
            #         tmp.append(lines[i + nextline * j].split()[1])
            #     band.append(tmp)

            for i in range(num_bands):
                tmp = []
                for j in range(num_kpt):
                    tmp.append(lines[j + nextline * i].split()[1])
                band.append(tmp)

            for i in range(num_kpt):
                ktraj.append(lines[i].split()[0])

        self.band = np.array(band, dtype='d')
        self.ktraj = np.array(ktraj, dtype='d')

        if gnu_plotdata is not None:
            with open(gnu_plotdata, 'r') as gnuset:
                lines = gnuset.readlines()
                ticks = []
                for x in lines:
                    if "xtics" in x:
                        ticks.append(re.findall(r"[A-Z]+", x))
                        ticks.append(re.findall(r"[0-9.]+", x))

            self.guideticks = ticks

    def gnuband(self, fermi, shift, guide):
        input_name = self.input_name

        if fermi is None:
            fermi_e = 0.0
        else:
            fermi_e = fermi

        # Shifting for the fermi level value
        # Extra shifting of vbm only if it is turned on
        if shift is True:
            self.band -= fermi_e

        def bandname():
            tmp_wavename = []
            for i in range(len(self.band)):
                tmp_wavename.append(" " + input_name + "_Band_" + str(i + 1))

            return tmp_wavename

        def itxheader(bandname):
            # Writing the header part of .itx
            out.write("IGOR\n")
            out.write("WAVES/D ")
            out.write(input_name + "_Band_kv")
            for x in bandname:
                out.write(x)
            out.write("\nBEGIN\n")

        def bandwave():
            # Writing the wave part of .itx
            for i in range(np.shape(self.band)[1]):
                out.write(str(self.ktraj[i]))
                for j in range(np.shape(self.band)[0]):
                    out.write(" " + str(self.band[j][i]))
                out.write("\n")
            out.write("END\n")

        def guidewave():
            # Line for the high-symmetry point guideline
            if guide is True:
                if self.guideticks is None:
                    guideline = []
                    for i in range(np.shape(self.band)[1]):
                        if i == 0:
                            guideline.append(self.ktraj[i])
                        elif self.ktraj[i] == self.ktraj[i - 1]:
                            guideline.append(self.ktraj[i])
                        elif i == (np.shape(self.band)[1] - 1):
                            guideline.append(self.ktraj[i])
                    guideline = np.array(guideline)

                else:
                    guideline = self.guideticks[1]

                out.write("WAVES/D ")
                out.write(" " + input_name + "_guide " + input_name + "_guide_y1 " + input_name + "_guide_y2\n")
                out.write("BEGIN\n")
                for i in range(len(guideline)):
                    out.write(str(guideline[i]) + " -30.00 30.00\n")
                out.write("END\n")

        def guide_textwave():
            if guide is True:
                if self.guideticks is not None:
                    out.write("WAVES/T ")
                    out.write(" " + input_name + "_guide_text\n")
                    out.write("BEGIN\n")
                    for x in self.guideticks[0]:
                        out.write('"' + str(x) + '"' + "\n")
                    out.write("END\n")
            else:
                pass

        def displayband(bandname, figurename=None):
            # Writing the graph plotting part of .itx
            tmp = "\nX Display" + "".join(bandname)
            limchar = 15
            if figurename is None:
                if len(bandname) <= limchar:
                    out.write(str(tmp))
                    out.write(" vs " + input_name + "_Band_kv")
                    out.write(" as " + ' \"' + "band_" + input_name + '\"' + "\n")

                else:
                    numline = math.ceil(len(tmp) / limchar)
                    numpart = math.ceil(len(bandname) / numline)

                    for i in range(int(numline)):
                        if i == 0:
                            out.write("\nX Display" + "".join(bandname[:numpart]))
                            out.write(" vs " + input_name + "_Band_kv")
                            out.write(" as " + '\"' + "band_" + input_name + '\"' + "\n")
                        elif len("".join(bandname[(i * numpart):(i * numpart + numpart)])) == 0:
                            pass
                        else:
                            out.write("X AppendToGraph" + "".join(bandname[(i * numpart):(i * numpart + numpart)]))
                            out.write(" vs " + input_name + "_Band_kv\n")

            else:
                if len(bandname) <= limchar:
                    out.write(str(tmp))
                    out.write(" vs " + input_name + "_Band_kv")
                    out.write(" as " + ' \"' + "band_" + figurename + '\"' + "\n")

                else:
                    numline = math.ceil(len(tmp) / limchar)
                    numpart = math.ceil(len(bandname) / numline)

                    for i in range(int(numline)):
                        if i == 0:
                            out.write("\nX Display" + "".join(bandname[:numpart]))
                            out.write(" vs " + input_name + "_Band_kv")
                            out.write(" as " + '\"' + "band_" + figurename + '\"' + "\n")
                        elif len("".join(bandname[(i * numpart):(i * numpart + numpart)])) == 0:
                            pass
                        else:
                            out.write("X AppendToGraph" + "".join(bandname[(i * numpart):(i * numpart + numpart)]))
                            out.write(" vs " + input_name + "_Band_kv\n")

        def displaypreset():
            preset = ("X DefaultFont/U \"Times New Roman\"\n"
                      "X ModifyGraph width=255.118,height=340.157\n"
                      "X ModifyGraph marker=19\n"
                      "X ModifyGraph lSize=1.5\n"
                      "X ModifyGraph tick(left)=2,tick(bottom)=3,noLabel(bottom)=2\n"
                      "X ModifyGraph mirror=1\n"
                      "X ModifyGraph zero(left)=8\n"
                      "X ModifyGraph fSize=28\n"
                      "X ModifyGraph lblMargin(left)=15,lblMargin(bottom)=10\n"
                      "X ModifyGraph standoff=0\n"
                      "X ModifyGraph axThick=1.5\n"
                      "X ModifyGraph axisOnTop=1\n"
                      "X Label left \"\Z28 Energy (eV)\"\n"
                      "X ModifyGraph zero(bottom)=0;DelayUpdate\n"
                      "X SetAxis left -3,3\n"
                      "X ModifyGraph zeroThick(left)=2.5\n")

            preset_guide = ("\nX AppendToGraph " + input_name + "_guide_y1 " + input_name + "_guide_y2 vs " +
                            input_name + "_guide\n"
                            "X ModifyGraph mode(" + input_name + "_guide_y1)=1,rgb(" + input_name + "_guide_y1)=(0,0,0)\n"
                            "X ModifyGraph mode(" + input_name + "_guide_y2)=1,rgb(" + input_name + "_guide_y2)=(0,0,0)\n"
                            "X SetAxis left -3,3"
                            )

            preset_guide_text = ("\nX ModifyGraph userticks(bottom)={test_guide,test_guide_text}\n"
                                 "X ModifyGraph noLabel=0\n")

            out.write(preset)
            if guide is True:
                out.write(preset_guide)
                if self.guideticks is not None:
                    out.write(preset_guide_text)

        with open(self.outfile, 'w') as out:
            # Writing the itx file
            wavename = bandname()
            itxheader(wavename)
            bandwave()
            guidewave()
            guide_textwave()
            displayband(wavename)
            displaypreset()
            return


def executescript(args):
    p = gnu2igor(args.output)
    p.gnuband_parser(args.xdata, args.ydata, args.gnudata)
    p.gnuband(args.fermi, args.shift, args.guide)
    return


def main():
    # Main parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-x", dest="xdata", type=str, default="wannier90_band.kpt")
    parser.add_argument("-y", dest="ydata", type=str, default="wannier90_band.dat")
    parser.add_argument("-p", dest="gnudata", type=str, default="wannier90_band.gnu")
    parser.add_argument("-o", dest="output", type=str, default="band.itx")
    parser.add_argument("-f", dest="fermi", type=float, default=0.0)
    parser.add_argument("-s", dest="shift", action="store_true")
    parser.add_argument("-g", dest="guide", action="store_true")
    parser.set_defaults(func=executescript)

    args = parser.parse_args()

    try:
        getattr(args, "func")
    except AttributeError:
        parser.print_help()
        raise AttributeError("Error!")
    args.func(args)


if __name__ == "__main__":
    main()
