---
toc: true
description: A checklist to have when thinking of implementing crypto
categories: [crypto]
---
# An opinonated checklist on crypto

{% include alert.html text="Please don't roll your own crypto, just.. don't do it." %}

Ohkay, so you are not heeding the warning ha, let's see how we can minimize the damage then..

This is sort of a checklist of things to verify in crypto implementations on first glance. Most of these are guidelines from Owasp  [^1] and a few from other sources. Whenever I study a crypto implementaton these are things I first check some of these guidelines. They are obvious, even mundane and some may be different depending upon the circumstances.

For example, guidelines for hash lengths, key lengths etc. will depend on how and where the crypto is implemented and cannot be considered as a hard and fast rules.

## Types

- **Application level** - Closest to source, most desired, ensure usage of established algorithms suchs a openSSL, libreSSL, and use approved APIs, may need more memory/processing bandwidth.
- **Protocol level** - The next level where the protocol ensures encryption, eg: HTTPS using SSL, when mutual authentication is required, care should be taken as there are two session keys for each side (client –> server and server –> client)
- **Network level** - The next level, protects both protocol and application level with no need for any level of encryption at that level. Typicall example is IPSec VPN, can be used to create a secure tunnel to connect to a network etc.

## keys

- Symmetric keys should be at least 256 bit in length, possibly 512 for critical applications
- Hash length - 128 is okay for most applications, 256 is the way to go if a method authentication is being used
- Asymmetric keys 1024 bit is okay for normal applications, 1536 or 2048 for critical applications, for the paraniod 4036

## Key Storage

- Check who all have access to the keys
- Check if the keys can be exported/imported without a password
- Check if keys are stored in code - this can be bad in two ways, one the key can be exploited by anyone having access to source code. Second, if key rotation is needed or if keys become pulbic it would be difficult to change the key.

## How to protect one self

- Make sure the access is the least level of required access and not further
- Make sure keys are not exportable (marked as non exportable) when signing requests are generated.
- Once imported to keystore, destroy the file (certificate) that was imported, stored in the file system
- Log any change to keys
- Use secure passphrases for keys stored
- Stop storing keys in code files/binaries
- Give minimum access to applications that use keys to do something
- Always ask for a passphrase when user interaction is available

## Transmission of data

- Assess the levels of trust we can have/we need to have on data transmitted
- Always encrypt sensitive data before transmission
- Encrypt as close to source as possible
- All paths should be covered with same level of encryption
- Identify if any temporary files/garbage collected data is written when encrypting/decrypting if so see who all has access to it
- Pick an adequate level of encryption - Algorithm and key strength according to accessment done of levels of trust

## Session Tokens

- Ensure session tokens are truly random eg use `/dev/urandom` to create UUIDs etc
- Never use static UUID where security is needed
- Do not use sequential values to maintain session as this can be easily spoofed
- Check from where keys are generated for session maintainance (Are they coming from random source?)

## Don't do this

- **Message authentication using md5** -  Md5 mac when used to authenticate message using a shared secret is vulnerable to length extension attacks.

These attack works as follows:

    Consider there is a shared secret a user and server is having
    User authenticates data sent using the scheme:

    "DATA"+md5(shared_secret+"DATA")

This was a common form of MAC a few years back.

It has been found that it is trivial to create a valid MAC (Message Authentication Code) based on md5 by simply extending the hash. For example,

    "DATA"+"CRAFTED_DATA"+md5(shared_secret+"DATA"+"CRAFTED_DATA")

Will be accepted by the server as successfully authenticated in some cases, as we can see, the attacker do not need to know the `shared_secret` but merely can extend the hash. [^1]


{% include alert.html text="Thus do not use md5 as a mac" %}


- **Using equality operator with HMAC for message Authentication** - Vulnerable to timing attacks, this is because it takes slightly longer to match correct characters, than for wrong characters when equality operator is used to compare.

An attacker can simply bruteforce the hmac with something like: 


    Consider the hmac is bxyz5

    The attacker can then send a string aaaaa to zzzzz first, when the average response time is considered the attack with
    string baaaa would take a slightly longer time that a---- , thus the attacker now possess the first character of the mac,
    this can be repeated to get the entire hmac, thus this simple mistake of using equality operator for comparison can lead 
    to a vulnerability if the attacker is motivated enough.


To prevent timing attacks do not use equality operator but XOR each byte as:

```python
a XOR a = 0
```
Sum up for all the bytes and if the result is 0 then, the hmac is identical and we have verified the authenticity of the message.

In python use something like:

```python
hmac.hexcompare(a, b)
```
To reduce the chance of timing attacks, this function can only be used if both a and b are ASCII coded.

## The end

Here are some more refereneces to get you started, good luck!

1. [Bad crypto practices](https://web.archive.org/web/20170206210656/http://www.happybearsoftware.com/you-are-dangerously-bad-at-cryptography.html)
2. [Cryptographic right answers](http://www.daemonology.net/blog/2009-06-11-cryptographic-right-answers.html)
3. [Crypto coding rules](https://github.com/veorq/cryptocoding)
4. [Matasano crypto challenges](https://blog.pinboard.in/2013/04/the_matasano_crypto_challenges/)
5. [Confidentiality is not authentication](https://paragonie.com/blog/2015/05/using-encryption-and-authentication-correctly)


[^1]: https://bit.ly/2W0dZum
