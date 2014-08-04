# The following pages may help if there are any errors: http://www.statmt.org/moses/?n=Development.GetStarted, http://www.statmt.org/moses/?n=Moses.ExternalTools#ntoc3, http://www.statmt.org/moses/?n=FactoredTraining.BuildingLanguageModel#ntoc4
# PLEASE READ ALL INSTRUCTIONS IN TEH COMMENTS

# Install dependencies
sudo apt-get update
# for ubunutu 14.04
sudo apt-get install build-essential g++ git subversion automake autotools-dev libicu-dev libtool zlib1g-dev libboost-all-dev libbz2-dev liblzma-dev python-dev cmake libtcmalloc-minimal4
# for other ubuntus
# sudo apt-get install build-essential g++ git subversion automake autotools-dev libicu-dev libtool zlib1g-dev libboost-all-dev libbz2-dev liblzma-dev python-dev cmake libtcmalloc-minimal0

# Create directory for all of Moses tools
mkdir translation_tools
cd translation_tools

#Any references to -j8 replace with the correct number of threads you want to run with

# If your default version of boost is Boost 1.48, it has a bug so download and build Boost manually
# user `dpkg -l '*boost*'` to find out what version of boost you have

# wget http://downloads.sourceforge.net/project/boost/boost/1.55.0/boost_1_55_0.tar.gz
# tar zxvf boost_1_55_0.tar.gz
# cd boost_1_55_0/
# ./bootstrap.sh
# ./b2 -j8 --prefix=$PWD --libdir=$PWD/lib64 --layout=tagged link=static threading=multi,single install || echo FAILURE
# cd ..
# rm boost_1_55_0.tar.gz

# Download and build the correct IRSTLM
wget http://sourceforge.net/projects/irstlm/files/latest/download
tar zxvf download
cd irstlm-5.80.03/
./regenerate-makefiles.sh
./configure --prefix=$PWD
make -j8
make install
cd ..
rm download

# Download and install MGIZA. Download the most up to date version from this site: http://www.kyloo.net/software/doku.php/mgiza:overview
wget http://sourceforge.net/projects/mgizapp/files/mgizapp-0.7.3-updated.tgz/download
tar zxvf download
cd mgizapp/
cmake .
make
make install
# The above may fail. It appears that the following will fix the issue. (http://www.kyloo.net/software/doku.php/mgiza:fixing_boost_library)
# In CMakelists.txt change SET(MGIZA_VERSION_PATCH "0") to SET(MGIZA_VERSION_PATCH "2")
# and
# change FIND_PACKAGE( Boost 1.46 COMPONENTS thread) to FIND_PACKAGE( Boost COMPONENTS thread system)
#
# also in src/mkcls/myleda.h, line 221 change
# insert(typename MY_HASH_BASE::value_type(a,init));
# to
# this->insert(typename MY_HASH_BASE::value_type(a,init));

cd ..
rm download

# Download and build Moses
git clone https://github.com/moses-smt/mosesdecoder.git
cd mosesdecoder/
mkdir tools
cp ../mgizapp/bin/* tools/
cp ../mgizapp/scripts/merge_alignment.py tools/

#If you replaced boost, use this and replace all pathnames with the appropriate ones based on your installation
# ./bjam --with-boost=/home/ubuntu/translation_tools/boost_1_55_0 --with-irstlm=/home/ubuntu/translation_tools/irstlm-5.80.03 --with-giza=/home/ubuntu/translation_tools/mgizapp/bin -j8 -a -q
#Otherwise use this:
./bjam --with-irstlm=/home/ubuntu/translation_tools/irstlm-5.80.03 --with-giza=/home/ubuntu/translation_tools/mgizapp/bin -j8 -a -q

# If you don't want to accidentally turn backticks (`) into apostrophes ('), then comment out line 278 of translation_tools/mosesdecoder/scripts/tokenizer/tokenizer.perl
# $text =~ s/\`/\'/g;

# Test moses is working properly
wget http://www.statmt.org/moses/download/sample-models.tgz
tar xzf sample-models.tgz
cd sample-models
../bin/moses -f phrase-model/moses.ini < phrase-model/in > out
#If you look in the file `out` it should say this is a small house
cd ..
rm sample-models.tgz
