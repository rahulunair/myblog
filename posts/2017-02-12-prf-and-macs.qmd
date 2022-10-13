---
toc: true
description: Pseudo random functions and message authentication.
categories: [crypto]
---
# Message Authentication and PRFs

{% include info.html text="Alice wants to talk to Bob" %}

<p align="center">
<img src="https://imgur.com/ZiOuEd1.png"/>
</p>

Bob gets a message from Alice, as Bob doesn’t think a girl like **Alice** would talk to him, he wants Alice to authenticate or convince him that it is indeed she who is talking.

## How will she do it?

Well one way to do it is, if she has some secret already shared with Bob, and use it to seed a pseudo random number generator (PRG) that they built at a recent rasberry pi conference, both of them attended and use the number to validate it is indeed Alice.

She could seed as the input of the PRG, run it for 10 times chaining the seed each time and get the 10th random number. She can casually write down this number on a note and put it in Bob’s bag.

Bob finds the note, supposedly from Alice, in his bag. He follows the instructions (as any boy would), on how to generate the 10th random number from the shared secret and compares it with the random number that was written at the end of the note.

Now, assuming Bob didn’t screw up generating the random number, he knows for a fact that it is indeed Alice who left the note as only she knew the ‘secret’ that was used to seed the random number. Bob is happy..

This is cool and all, but they haven’t really talked till now. If they have to talk with **authentication**, then both of them will have to remember how many rounds the PRG ran and keep a tab on this as long as they want to talk, thus they have to maintain a ‘state’, that’s not fun!!.

## Let's see an example

Alice intiates,

10th iteration of the random number generator:

```python
Random Number - R10
Alice - A
Bob - B

A --(R10)--> B
B --(generates R10 and matches it with Alice)
```
Next time, when Bob responds with a encoded secret, both of them have to iterate the random number generator for the 11th time.

```python
B --(R11)--> A
A --(generates R11 and matches it with Bob's R11)
```
As you can see both Alice and Bob have to remember how many times they have ran the PRG (maintain a state) and that is not fun.

## What can they do to avoid maintaining the state?

Well, one thing they can do is to use a ‘special’ family of pseudo random functions (PRF) called the HMAC-HASH function.

Whoa!! what the heck is a PRF? you ask.

A PRF or a Pseudo Random Function [^1] is a family of functions that if given, there is no method that can be used to distinguish it from another function from the same family, in the same domain. By this I mean, there is no sane way before hell freezes over that you can get any information if you were given outputs of two functions from the same family to tell which one is which.

So coming back to HMAC-HASH. `HMAC` or Hash based Message Authentication Code is a type of `PRF`, which you can use to authenticate yourself to a person, if both of you have a shared-secret. The HASH here can be `MD5` or `SHA1` or `SHA256` or something like that.

## Is this secure?

For now, there are no [known attacks against](http://crypto.stackexchange.com/questions/9336/is-hmac-md5-considered-secure-for-authenticating-encrypted-data), `HMAC-MD5` [^2] or HMAC-SHA1, but that doesn’t mean there will never be, so please don’t use it okay? please...

Okay, all I want to know how Bob can talk to Alice and authenticate that the message is indeed from Bob, how will he do that?

## Hmm… ahh, impatience...

Well, Bob could use **HMAC-SHA2** [^3] authentication function, hash the message he is sending to Alice using the **shared-secret**. She would be able to verify if the message is indeed from Bob by hashing it with **HMAC-SHA2** using the shared-secret as the key and comparing the hashes, both should be same.

## The end

Hope this helps Bob.

[^1]: http://crypto.stackexchange.com/questions/31343/what-is-the-purpose-of-pseudorandom-function-families-prfs
[^2]: http://crypto.stackexchange.com/questions/9336/is-hmac-md5-considered-secure-for-authenticating-encrypted-data
[^3]: http://security.stackexchange.com/questions/33123/hotp-with-as-hmac-hashing-algoritme-a-hash-from-the-sha-2-family
