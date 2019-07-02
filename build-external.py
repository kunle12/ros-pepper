#!/usr/bin/env python

import os
import sys
import re
import shutil
import urllib2
import zipfile
import subprocess

try:
        import yaml
except:
        sys.exit("""Python could not find a yaml parser!
    Install it with the command: pip install pyyaml --prefix=/home/[username]/.local""")

if not 'ROS_WORKSPACE_ROOT' in os.environ:
    print('Environment variable ROS_WORKSPACE_ROOT not set. Please set it to workspace where ROS will be built.')
    sys.exit()

path = os.environ['ROS_WORKSPACE_ROOT']

def setup():
    os.chdir(path)
    if not os.path.isdir('external'):
        make_directory('external')

def make_directory(directory):
    try:
        os.mkdir(directory)
    except OSError:
        pass#print('\t[WARN] Attempting to make directory that already exists: {}'.format(directory))

def cleanup():
    os.chdir(path)
    system_call('rm -rf external')

def system_call(command):
    command = os.path.expandvars(command)

    DEVNULL = open(os.devnull, 'w')

    process = subprocess.Popen(command.split(), env=os.environ, stdout=DEVNULL, stderr=subprocess.PIPE)
    result_code = process.wait()

    if result_code != 0:
        raise Exception('Failed to process command {} ({}) with error: {}'.format(command, result_code, process.communicate()[1]))

def download(uri, local_name, retries=3):
    if not local_name:
        local_name = url.split('/')[-1]
    
    try:
        req = urllib2.urlopen(uri, capath="/etc/ssl/certs")
        chunk = True

        with open(local_name, 'wb') as f:
            for chunk in iter(lambda: req.read(1024*16), ''):
                f.write(chunk)
    except Exception as e:
        os.remove(local_name)
      
        if retries > 0:
            print('\t\tFetch failed. Retrying... (Attempt {} of 3)'.format(4 - retries))
            return download(uri, local_name, retries - 1)
        else:
            raise Exception('Failed to download package from {} with error: {}'.format(uri, str(e)))

def fetch(uri, name):
    print('\tFetching {}'.format(uri))
    os.chdir('{}/external'.format(path))

    if not os.path.isfile(name):
        download(uri, name)
        #system_call('wget {} -O {}'.format(uri, name))
    else:
        print('\tAlready fetched. Skipping...'.format(uri.split('/')[-1]))

def unpack(compressed, to):
    print('\tUnpacking {}'.format(compressed))

    os.chdir('{}/external'.format(path))
    if compressed.endswith('.gz') or compressed.endswith('.tgz'):
        make_directory(to)
        system_call('tar xvfz {} -C {} --strip-components 1'.format(compressed, to))
    elif compressed.endswith('.bz2'):
        make_directory(to)
        system_call('tar xvfj {} -C {} --strip-components 1'.format(compressed, to))
    elif compressed.endswith('.zip'):
        if os.path.exists(to):
            shutil.rmtree(to)

        make_directory(to)
        zipped = zipfile.ZipFile(compressed, 'r')
        zipped.extractall()
        os.rename(zipped.namelist()[0], to)
    else:
        os.chdir(path)
        raise Exception('Unknown file compression type: {}'.format(compressed))
    
    os.chdir(path)

def build(package, method, flags, make_flags='-j4'):
    print('\tBuilding {}'.format(package))

    os.chdir('{}/external/{}/'.format(path, package))

    if method == 'python':
        if not os.path.isdir('{}/ros_toolchain_install/lib/python2.7/site-packages/'.format(path)):
            os.makedirs('{}/ros_toolchain_install/lib/python2.7/site-packages/'.format(path))

        system_call('python setup.py install --prefix={}/ros_toolchain_install'.format(path))
        os.chdir(path)
        return

    print('\t\tConfiguring...')

    if method == 'configure':
        system_call('./configure --prefix={}/ros_toolchain_install/ {}'.format(path, flags))

    elif method == 'cmake':
        make_directory('build_directory')
        os.chdir('build_directory')
        system_call('cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX={}/ros_toolchain_install/ -DCMAKE_INSTALL_LIBDIR=lib {} ..'.format(path, flags))
    elif method == 'custom':
        system_call(flags)
    elif method == 'make':
        pass
    else:
        raise Exception('Unknown configuration method: ' + method)

    print('\t\tMaking...')
    system_call('make {}'.format(make_flags))

    print('\t\tInstalling...')

    if method == 'make':
        system_call('make prefix=/{}/ros_toolchain_install/ install'.format(path))
    else:
        system_call('make install')

    os.chdir(path)

def patch(patch_file):
    print('\tApplying patch: {}'.format(patch_file))

    if not os.path.isfile('patches/{}'.format(patch_file)):
        raise Exception('Patch file missing: ' + patch_file)

    os.chdir('{}/external'.format(path))

    try:
        system_call('patch -N -s -p0 -i ../patches/{}'.format(patch_file))
    except:
        print('\tAlready patched. skipping...')

    os.chdir(path)

if (len(sys.argv) == 1):
    print('Invalid arguments. Missing input file.')
    sys.exit()

os.environ.update({
    'PYTHONPATH': os.path.expandvars('$ROS_WORKSPACE_ROOT/ros_toolchain_install/lib/python2.7/site-packages/:{}'.format(os.environ['PYTHONPATH']))
})

packages = yaml.load(open(sys.argv[1], 'r'))

setup()

try:

    for package in packages:
        uri = package['package']['uri']
        name = package['package']['name']

        compressed = name + os.path.splitext(uri)[1]

        method = package['package']['method']

        try:
            flags = package['package']['flags']
        except KeyError:
            flags = ''

        
        try:
            make_flags = package['package']['make_flags']
            if not '-j' in make_flags:
                make_flags += ' -j4'
        except:
            make_flags = '-j4'

        print('Package {}'.format(name))

        fetch(uri, compressed)
        unpack(compressed, name)

        try:
            patch(package['package']['patch'])
        except KeyError:
            pass

        try:
            system_call(package['package']['prepare'])
        except KeyError:
            pass

        build(name, method, flags, make_flags)

        try:
            system_call(package['package']['teardown'])
        except KeyError:
            pass

except Exception as e:
    print('Building external dependencies failed with error: {}'.format(str(e)))
    sys.exit(1)

#cleanup()
