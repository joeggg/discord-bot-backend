set -e

# Assumes token already there and you have root privileges over ssh
TARGET="$1"
FOLDER="worker-copy"
FILES="bot_worker/ config/ data/ scripts/ pyproject.toml poetry.lock README.md"

ssh $TARGET "rm -rf $FOLDER && mkdir $FOLDER"
scp -r $FILES $TARGET:~/$FOLDER
ssh $TARGET "pushd $FOLDER; chmod +x scripts/install.sh; scripts/install.sh; popd; rm -rf $FOLDER"
echo "Finished deploy"
