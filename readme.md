# GraphAPet (Back-end)
GraphAPet back-end is *wip* project that I'm developping in my free time.
It should work as a platform to help people find a pet in their vicinity or to keep track of your pets medication / events / vet appointments. 

This part is the core of the applciation, it manage every user and evry business logic. 
I serve as a skeleton for the app.


## Installation 
Clone this repo to your device.
I suggest to create a virtual environment 

once you have cloned the repo, by enteryng the project folder install the requirments by using the package manager [pip](https://pip.pypa.io/en/stable/)
and add the `-r` parameter so it will recursively add every needed module.

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
If you want to recive notification via telegram create a bot with the help of [BotFather](https://web.telegram.org/z/#93372553), then take the token it gives you and save it in `config.yml` file under the voice *telegram*
Be sure to add your contact id in the `admin` field so you will recive the message
to get it you can look up for the [@RawDataBot](https://web.telegram.org/z/#211246197) in telegram and starting the conversation. 
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
If you don't want or can't use telegram just set the `active` field to `False` and no bot will be activated

### firebase bucket
to save the media that users will send, I usually create a bucket on firebase. 
So create your project on the firebae console and get your authentication key ( i usually store it in the root folder )

Then from the firebase console create a new bucket and save the uri.

## Basic structure
Since i came from a node.js development team I inherited some infrastructure basis. 
For instance i divided the server into 3 main layer : 
1. API
2. DOMAIN
3. DATA

and each one shoul be as indipendand as possible from the others, so if i change the DB, and migrate from PostgreSQL to mongoDB, the domain layer and dataLayer should function as nothing happend.
If i want to migrate from postgresql to REST API the data layer and domani layer should work like nothing happend
If i want some change in the logic that rule the server it should suffice change the domain layer, leaving API and DATA untouched.

### API layer
The first level shoul funciton as an entry level for all the incominc request, it decide what enters and what exit. 
I'm trying to do the very minimal here, like just saying "if the user ask for A, the server will responde with A, or if something gose wrong, with this error". 

So every function is wrapped in a ` try except` block so i'm always _-(or at least  most of the time)-_ in control over eventual errors.

There is a middleware that check if the users are enabled or not to do the action they have required and i'm using a decorator to have a more clean function.
 I would have loved to use decorator on every query and mutation like i did with the resolvers :
 ```python
@query('operetionA')
@auth_middleware
operation_a():
    try:
        #soome stuff
    except Exception as e:
        #return error
 ```
but unfortunately I can't declare the QueryType or MutationType in a file and call-it to another to add fields and then add it to the `make_executable_schema` method.
So i Created the `operation.py` to group them all in a single file, including every resolver.


### DOMAIN layer
Here goes theapplication business logic.
Here should go what the application need to do in order to complete the request. 
Like if a user is signing UP, here is where you should trigger the event of sending an e-mail to him with che verification code.
Or if a user is adding a pet to him-self then here is where you first call the *DATA* method to create the pet, and then call de *DATA* method to create a new ownership.

It would be best if this level does not chage how the users call a method or how the data Layer fetch the data. 

### DATA layer
This is where the data are saved and fetched. 
This should just be used as a method to retrive data given some option like "the name of the user i'm looking for is 'Enzo'", this layer should not have any business logic operation, only saving or fetching data should be allowed here.
Since we are using a SQL like db i created a method to query the db in a way that should suffice for every future entity.
I divided pagination ordering and filers so that every itmes could be searched the same way: 
- pagination: 
    - `page_size`: determs the `lIMIT` sql parameter, by default set to 20
    - `page`: moltiply this value with page_size and you obtain the `SKIP` parameter, by default set to 0
- ordering: 
    - `order_by`: the name of the primary column to order items, by defoult is set to `created_at`
    - `order_direction`: ASC or DESC to tedermin how items should be ordered,  by defoult `ASC`
- filters: 
    this include for the main entity the `search` and `search_columns` property
    - `search`: text to look in the columns selected by `search_columns`, by default is an empty string
    - `search_columns`: array of strings that will be used to look for the text insered in `search` field
    - `filters`: 
        - `fixeds`: 1 to 1 match on the selected column and value _user.name = 'Enzo'_ 
        - `ranges`: min and max value for the column to match, if only one is set is lik sayng, everything tha id more ( or less ) the the selected value
        - `lists` : list of value the selected column can be setto be mached by the request _USER.role in ('ADMIN', 'USER')_ 
        - `join` : with this you can duplicate the `filters` structure to a child of the main entity, like from `OWNERSHIP` you can go down and filter `PET` or `USER`, and so on to every "children"