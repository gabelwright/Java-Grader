import subprocess
import os
import sys

testfiles = ['test1.java']
folder_directory = '/Users/m.wright/Desktop/Fraction'


def writeJavaFile(file, testfile):
    txtFile = open(file, 'r')
    txtContents = txtFile.read()
    txtContents = txtContents.replace(
        'public class Fraction', 'class Fraction')
    txtFile.close()

    mainTxt = open(testfile, 'r')
    main_method = mainTxt.read()
    mainTxt.close()

    javaFile = open('ActiveFile.java', 'w')
    javaFile.write(main_method)
    javaFile.write(txtContents)
    # javaFile.write('}')
    javaFile.close()


def compileJava():
    output = ''
    try:
        subprocess.check_output(['javac', 'ActiveFile.java'], stderr=subprocess.STDOUT).communicate()[0]
        
    except subprocess.CalledProcessError as e:
        err_message = e.output
        output += "Error with file:\n%s\n" % err_message
    except Exception, e:
        subprocess.check_output(['javac', 'ActiveFile.java'])
        output += subprocess.check_output(['java', 'ActiveFile'])

    try:
        if os.path.isfile('ActiveFile.class'):
            os.remove('ActiveFile.class')
        if os.path.isfile('ActiveFile.java'):
            os.remove('ActiveFile.java')
        if os.path.isfile('Fraction.class'):
            os.remove('Fraction.class')
    except:
        print("Could not delete files")

    return output


def delete_files():
    if os.path.isfile('ProgramResults.txt'):
        os.remove('ProgramResults.txt')
    if os.path.isfile('ActiveFile.java'):
        os.remove('ActiveFile.java')
    if os.path.isfile('Fraction.class'):
        os.remove('Fraction.class')


fileList = []
delete_files()

for file in os.listdir(folder_directory):
    if file.endswith('.txt'):
        fileList.append(file)

outputFile = ''

for file in fileList:
    outputFile += file + '\n'
    for test in testfiles:
        writeJavaFile(file, test)
        outputFile += compileJava()
        outputFile += '\n'

finalSolutions = open('ProgramResults.txt', 'w')
finalSolutions.write(outputFile)
finalSolutions.close()

subprocess.call(['open', '-a', 'TextEdit', 'ProgramResults.txt'])
