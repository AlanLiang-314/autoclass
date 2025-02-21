# Autoclass
A script designed for the CCU course selection system to automatically select courses

**Use at your own risk**

## Usage
1. Install the required packages
```bash
pip install -r requirements.txt
```
2. Download the edge driver from [here](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) and put it in the `autoclass/edgedriver` directory

3. Create .env file in the `autoclass` directory and fill in the following information
```bash
USERNAME=your_username
PASSWORD=your_password
```

4. change settings in `autoclass/autoclass.py` if needed

5. Run the script
```bash
python autoclass/autoclass.py
```