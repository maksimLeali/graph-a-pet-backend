# Pet finder (Back-end)
Pet finder backend is *wip* project that i'm developping in my free time.

## Installation 
Clone this repo to your device.
I suggest to create a virtual environment 

once you have cloned the repo, by enteryng the project folder install the requirments by using the package manager [pip](https://pip.pypa.io/en/stable/){:target="\_blamk"}
and add the ```-r``` parameter so it will recursively add every needed module.

```bash
pip install -r requirments.txt
```
if you don't have the python path variable setted use this instead

```bash
python3 -m pip intall -r requirments.txt
```

## Environment variable

Since i can't public everyprivate key but i want to let you know what variable are used in the project i made a `config_fileds.yml` file that will contain every variable name and path, but not the values

To make it work you will need to add a `config.yml` file on the root of the project ( same folder as `config_fileds.yml`)

### telegram
If you want to recive notification via telegram create a bot with the help of [BotFather](https://web.telegram.org/z/#93372553){:target="\_blamk"}, then take the token it gives you and save it in `config.yml` file under the voice *telegram*
Be sure to add your contact id in the `admin` field so you will recive the message
to get it you can look up for the [@RawDataBot](https://web.telegram.org/z/#211246197){:target="\_blamk"} in telegram and starting the conversation. 
It should respond you with  a structure like that: 
```
{
    "update_id": ~,
    "message": {
        "from": {...}
        "chat": {
            "id": <CHAT_ID>,
            "first_name": ~,
            "last_name": ~,
            "username": ~,
            "type": ~
        },
        ...
    }
}
```
save the `CHAT_ID` and add it to the telegram variable `adminId`

```
telegram: 
    active: True
    token: <YOUR_TOKEN> 
    adminId: <CHAT_ID>
```
If you don't want or can't use telegram just set the `active` to `False`