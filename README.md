# Home Entertainment Monitor

Microservice for controlling, monitoring and synchronizing my home entertainment
systems – LG OLED TV, Onkyo Receiver, and a Windows PC.

## Prerequisites

1. [Python 3.7](https://www.python.org/downloads/) or later is required.

2. Use [pip](https://pypi.org/project/pip/) to install the dependencies:

   ```shell
   pip3 install aiohttp aiopylgtv
   ```

## How to use?

1. Checkout the repository:

   ```shell
   git clone https://github.com/Samarkin/HomeEntertainmentMonitor
   cd HomeEntertainmentMonitor
   ```

2. Adjust the constants section in [monitor-tv-apps.py](./monitor-tv-apps.py)
according to your home setup.

3. Start the script:

   ```shell
   ./monitor-tv-apps.sh
   ```

   Note: Before adding the script to the LXSession autostart, consider removing
   all print statements to avoid over-logging.

## Why?

I'm not the kind of person who would use two remotes, or walk all the way to the
PC to turn it on.

## FAQ

### Would it work for me?

Probably not, but github is a good place to share the code between my laptop and
Raspberry Pi (where this code runs).

You could also use it as an example (and inspiration) to automate your own home
entertainment systems.

### Why there is a shell script along with the Python file?

Because Python is a really bad tool for writing long-running services –
the script sometimes crashes and I couldn't figure out why. The shell script
just restarts it.

I will eventually rewrite it in Go or Rust.
