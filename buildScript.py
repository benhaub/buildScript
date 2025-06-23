################################################################################
#Date: April 13th, 2025                                                        #
#File: buildScript.py                                                          #
#Authour: Ben Haubrich                                                         #
#Synopsis: Convenience script for executing various actions for the application#
################################################################################
import argparse
import subprocess
from shutil import which, rmtree
from os import rename, remove, chdir, environ
from pathlib import Path
from platform import system
from getpass import getuser

executableName = "appName"

"""
Sometimes the name that you use to search on your system with `which` is not the same as the name that is used to install the program.
This function converts from the name you used to search with `which` to the name used to install.
"""
def installationName(programName):
   if system() == 'Darwin' or system() == 'Linux':
      if 'ninja' == programName:
         return 'ninja-build'

   return programName

def installProgram(systemName, programName):
   if systemName == 'Darwin':
      if None == which(programName):
         print('Installing: ' + programName)
         subprocess.run(["brew", "install", installationName(programName)])
   elif systemName == 'Linux':
      if None == which(programName):
         print('Installing: ' + programName)
         subprocess.run(["sudo", "apt", "install", installationName(programName)])

def setupForPlatform(systemName):
  rootPermissionRequired = False
  executableSuffix = '.elf'
  debugger = 'gdb'

  if systemName == 'Darwin':
      cxxCompiler = which('clang++')
      cCompiler =  which('clang')
      debugger = 'lldb'
      executableSuffix = '.Mach-O'

      requiredSoftware = ['cmake', 'ninja', 'git', 'openocd', 'wget']
      for software in requiredSoftware:
         installProgram(systemName, software)

      return systemName, cCompiler, cxxCompiler, executableSuffix, debugger, rootPermissionRequired

  elif systemName == 'Linux':
      cxxCompiler = which('g++')
      cCompiler =  which('gcc')
      #In order to run the operating system on linux with the real-time scheduler settings you must run as root.
      rootPermissionRequired = True

      requiredSoftware = ['cmake', 'ninja', 'git', 'openocd', 'wget']
      for software in requiredSoftware:
         installProgram(systemName, software)

      return systemName, cCompiler, cxxCompiler, executableSuffix, debugger, rootPermissionRequired

if __name__ == '__main__':

  parser = argparse.ArgumentParser(prog='buildScript.py',
                                       description='Run cmake projects for various platforms',
                                       epilog='Created by Ben Haubrich April 19th, 2024')
  #This first positional argument holds one or more arguments (nargs='+') so that when new positional commands are add below
  #They are contained within the list of arguments for the first positional argument. In this way, a list of possible
  #commands can be searched through by the name of the commands given.
  parser.add_argument('command', type=ascii, nargs='+', default='None',
                    help=argparse.SUPPRESS
                    )

  parser.add_argument('clean', type=ascii, nargs='?', default='None',
                    help='Clean up the files from the last build'
                    )
  parser.add_argument('build', type=ascii, nargs='?', default='None',
                    help='Build the project in the selected directory'
                    )
  parser.add_argument('run', type=ascii, nargs='?', default='None',
                    help='Run the executable on the current platform. Does not run for the target.'
                    )
  parser.add_argument('doxygen', type=ascii, nargs='?', default='None',
                    help='Build the Doxygen documentation'
                    )
  parser.add_argument('valgrind', type=ascii, nargs='?', default='None',
                    help='Run valgrind with the selected analyzer. default is memcheck.'
                    )
  parser.add_argument('clang-tidy', type=ascii, nargs='?', default='None',
                    help='Run clang-tidy.'
                    )
  parser.add_argument('cppcheck', type=ascii, nargs='?', default='None',
                    help='Run cppcheck.'
                    )

  parser.add_argument('-d', '--project-dir', default='.',
                    help='The directory to build the project which contains a top-level CMakeLists.txt. Defaults to current directory'
                    )
  parser.add_argument('-b', '--build-type', nargs='+', type=ascii, default='Debug',
                    help='Build version to build. Defaults to "Debug". Choose from: "Debug", "Release", "Sanitize"',
                    )
  parser.add_argument('-x', '--toolchain', nargs='?', type=ascii, default=None,
                    help='Use the specified toolchain file instead the system default.',
                    )
  parser.add_argument('-t', '--target', nargs='?', type=ascii, default=None,
                    help='Compile for the target given by target'
                    )
  parser.add_argument('-v', '--valgrind-check', nargs='+', type=ascii, default='memcheck',
                    help='Run valgrind. default is memcheck. Choose from: "memcheck", "cachegrind", "callgrind", "helgrind", "drd", "massif", "dhat"',
                    )
  parser.add_argument('-c', '--clang-tidy-check', nargs='+', type=ascii, default='cppcoreguidelines-*',
                    help='Run clang-tidy with one of the supported checks. default is cppcoreguidelines-*'
                    )
  parser.add_argument('-f', '--path-to-analyze', nargs='+', type=ascii, default=None,
                    help='Path to analyze for cppcheck and clang-tidy. default is None. Path may lead to a file or a directory.'
                    )

  args = parser.parse_args()

  #Uncomment for help with debugging.
  #print("{}".format(args))
  systemName, cCompiler, cxxCompiler, executableSuffix, debugger, rootPermissionRequired = setupForPlatform(system())
  if (args.target != None):
      buildDirectoryName = args.target.strip('\'') + '_build'
  else:
      buildDirectoryName = systemName + '_build'

  cmakeBuildDirectory = Path(args.project_dir + '/' + buildDirectoryName)

  if '\'clean\'' in args.command:
      if cmakeBuildDirectory.exists():
          rmtree(args.project_dir + '/' + buildDirectoryName)

  if '\'build\'' in args.command and '\'test\'' not in args.command:
      cmakeBuildDirectory.mkdir(parents=True, exist_ok=True)
      chdir(buildDirectoryName)

      cmakeCommand = ['cmake',
                      '-G Ninja',
                      '-DCMAKE_EXPORT_COMPILE_COMMANDS=1',
                      '-S' + '../' + args.project_dir.strip('\'')]
    
    if (args.toolchain != None):
        cmakeCommand.append('-DCMAKE_TOOLCHAIN_FILE=' + args.toolchain.strip('\''))
    else:
        cmakeCommand.extend(['-DCMAKE_C_COMPILER=' + cCompiler,
                             '-DCMAKE_CXX_COMPILER=' + cxxCompiler])

    if (args.target != None):
        cmakeCommand.append('-D' + args.target.strip('\'') + '=1')
            if (args.target.strip('\'') == 'Tm4c123'):
                installProgram(systemName, 'lm4flash')

    if (args.build_type[0].strip('\'').lower() == 'release'):
        cmakeCommand.append('-DRELEASE_BUILD=1')
    elif (args.build_type[0].strip('\'').lower() == 'sanitize'):
        cmakeCommand.append('-DSANITIZE_BUILD=1')
    elif (args.build_type[0].strip('\'').lower() == 'debug'):
        cmakeCommand.append('-DRELEASE_BUILD=0')

    subprocess.run(cmakeCommand)
    subprocess.run(['ninja']) 

    chdir('..')

  if '\'run\'' in args.command:
      if True == rootPermissionRequired and getuser() != 'root' and systemName == 'Linux':
          print("The operating system uses realtime scheduling which on this platform requires root permission.")
          print("https://stackoverflow.com/questions/46874369/thread-explicit-scheduling-posix-api-gives-error")
          exit()
      else:
          subprocess.run([buildDirectoryName + '/' + executableName + executableSuffix], shell=True)

  if '\'doxygen\'' in args.command:
      if which('doxygen') == None:
         print("Doxygen is not installed. Install it (Y/n)?")
         response = input()
         if 'Y' == response:
            installProgram(systemName, 'doxygen')
         else:
            exit()

     #In the Doxygen configuration file, set WARN_AS_ERROR = FAIL_ON_WARNINGS
      result = subprocess.run(['doxygen', 'Doxygen/Doxyfile'])
      if result.returncode != 0:
          print("Doxygen exited with failure. Please check the output for errors.")
          exit(result.returncode)
   
  if '\'valgrind\'' in args.command:
      if (rootPermissionRequired and getuser() != 'root'):
          print("Re-run with sudo to do valgrind tests")
          exit()

      if which('valgrind') == None:
         print("Valgrind is not installed. Install it (Y/n)?")
         response = input()
         if 'Y' == response:
            installProgram(systemName, 'valgrind')
         else:
            exit()

      subprocess.run(['valgrind',
                      '--tool=' + args.valgrind_check[0].strip('\''),
                      '--track-origins=yes',
                      '--leak-check=full',
                      '--read-inline-info=yes',
                      '-s', buildDirectoryName + '/' + executableName + executableSuffix])

  if '\'clang-tidy\'' in args.command:
      result = subprocess.run(['brew', '--prefix', 'llvm'], capture_output=True)
          if 0 != result.returncode:
              print("Clang-tidy is not installed. Install it (Y/n)?")
              response = input()
              if 'Y' == response:
                  installProgram(systemName, 'llvm')
              else:
                  exit()

      result = subprocess.run([result.stdout.decode('utf-8').strip() + '/bin/clang-tidy', 
                               '-p', buildDirectoryName,
                               '-checks=' + args.clang_tidy_check.strip('\''),
                               '-header-filter=.*',
                               '--warnings-as-errors=*',
                               args.path_to_analyze[0].strip('\'')])

      if result.returncode != 0:
          print("Clang-tidy found errors. Please review the output.")
          exit(result.returncode)
        
    if '\'cppcheck\'' in args.command:
        if which('cppcheck') == None:
            print("Cppcheck is not installed. Install it (Y/n)?")
            response = input()
            if 'Y' == response:
                installProgram(systemName, 'cppcheck')
            else:
                exit()

        result = subprocess.run(['cppcheck',
                                 '--check-level=exhaustive',
                                 '--enable=all',
                                 '--disable=missingInclude',
                                 '--inconclusive',
                                 '--error-exitcode=1',
                                 args.path_to_analyze[0].strip('\'')])

        if result.returncode != 0:
           print("Cppcheck found errors. Please review the output.")
           exit(result.returncode)
       
exit(0)
