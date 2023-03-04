set -e

NAME="bot-worker"
POETRY="/root/.local/bin/poetry"

if [ "$1" == "test" ]; then
    echo "Starting test install"
    LOG_DIR="./log"
    CFG_DIR="./secret"
    DATA_DIR="./data"
else
    echo "Starting systemd install"
    INSTALL_DIR="/opt/$NAME"
    LOG_DIR="/var/log/$NAME"
    CFG_DIR="/etc/$NAME"
    DATA_DIR="/var/lib/$NAME"

    echo "** Adding any required users **"
    if id $NAME &>/dev/null; then
        echo "User already exists"
    else
        echo "Creating $NAME user"
        if [ ! -d $INSTALL_DIR ]; then
            sudo mkdir $INSTALL_DIR
        fi
        sudo useradd -m -d $INSTALL_DIR $NAME
    fi
fi

echo "** Creating any required folders **"
# Tokens
if [ ! -d $CFG_DIR ]; then
    sudo mkdir $CFG_DIR
    sudo touch $CFG_DIR/google_key.json
    sudo touch $CFG_DIR/reddit_creds.json
fi
# Log dir
if [ ! -d $LOG_DIR ]; then
    sudo mkdir $LOG_DIR
fi
# Data dir
if [ ! -d $DATA_DIR ]; then
    sudo mkdir $DATA_DIR
fi
# Tracks dir
if [ ! -d "$DATA_DIR/tmp" ]; then
    sudo mkdir $DATA_DIR/tmp
fi

if [ "$1" != "test" ]; then
    if systemctl list-units --full -all | grep -Fq "bot-worker.service"; then
        sudo systemctl stop bot-worker.service
    fi

    echo "** Copying files **"
    sudo cp -r data/. $DATA_DIR
    sudo cp config/config.cfg $CFG_DIR 
    sudo cp scripts/bot-worker.service /etc/systemd/system
    sudo cp -r bot_worker $INSTALL_DIR
    # Add run script
    echo "$INSTALL_DIR/.venv/bin/python -m bot_worker" > run.sh
    sudo cp pyproject.toml poetry.lock README.md run.sh $INSTALL_DIR
    cd $INSTALL_DIR

    echo "** Installing dependencies**"
    # Add poetry to path
    sudo $POETRY config virtualenvs.create true
    sudo $POETRY config virtualenvs.in-project true
    sudo $POETRY install --without dev
    echo "Done installing"
    sudo chmod +x run.sh

    sudo chown -R $NAME $INSTALL_DIR $CFG_DIR $LOG_DIR $DATA_DIR
    sudo systemctl daemon-reload
    sudo systemctl restart bot-worker.service

    echo "Successfully installed service"
else
    echo "** Installing dependencies**"
    poetry install --without dev
    echo "TESTING=true .venv/bin/python -m bot_worker" > run.sh
    echo "Giving correct permissions to run script and log file"
    sudo chmod 777 log/
    sudo chmod +x run.sh
fi
