import subprocess
import os
import sys
import shutil

contains_static_methods = False

CURRENT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

UPLOAD_DIRECTORY = CURRENT_DIRECTORY + '/static/posts'


def writeJavaFile(user, raw_code):
    file_path = '%s/%s' % (UPLOAD_DIRECTORY,user)
    full_path = '%s/%s' % (file_path,'CodinBlog.java')

    if not os.path.exists(file_path):
        os.makedirs(file_path)
    javaFile = open(full_path, 'w')
    javaFile.write(raw_code)
    javaFile.close()


def compileJava(user):
    file_location = '%s/%s' % (UPLOAD_DIRECTORY,str(user))
    os.chdir(file_location)
    output = ''
    try:
        subprocess.check_output(['timeout','5','javac', 'CodinBlog.java'], stderr=subprocess.STDOUT)
        output += subprocess.check_output(['timeout','5','java', 'CodinBlog'])
        err_code = 0
    except subprocess.CalledProcessError as e:
        output += e.output
        err_code = e.returncode
        print output

    for the_file in os.listdir(file_location):
        file_path = os.path.join(file_location, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)
    
    return err_code,output


def delete_files():
    try:
        if os.path.isfile('CodinBlog.class'):
            os.remove('CodinBlog.class')
        if os.path.isfile('CodinBlog.java'):
            os.remove('CodinBlog.java')
        for file in os.listdir(folder_directory):
            if file.endswith('.class'):
                os.remove(file)
    except:
        print("Could not delete files")
    

def get_test_files():
    testfiles = []
    for file in os.listdir(folder_directory):
        if file.endswith('.java'):
            testfiles.append(file)
    return testfiles

