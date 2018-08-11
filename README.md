# Check if your friend's Facebook account has activated #
A small app for fun :)

**Situation**: one of your friend on Facebook has just deactivated his account and you would like to get notification when he/she activate their account.

**WARNING**: this action might make your account locked temporarily :))

## 1. Set up

- Enviroment: python 3.5
- Install required package

```
sudo apt install mailutils
sudo pip3 install lxml
```

## 2. Run
- First, generate encrypted your email password and facebook password with a secret key:
    + encrypt password:

    ```
    $ sudo python3 encrypt_password.py e <secret_key> <your_password>
    (example result)
    $ sKtwpzCoMKewpfCtcK9wr7Cgms= 
    ```

    + decrypt password:
     
    ```
    $ sudo python3 encrypt_password.py d <secret_key> <encrypted_password>
    (example result)
    $ 123456
    ```

- Use this result to update `setting.ini`

- Run the checking

```
$ sudo python3 check.py <watching_account> <current_status> <days_to_watch> <secret_key>

$ sudo python3 check.py thongocngatho a 7 123
```