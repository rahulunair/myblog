---
toc: false
description: A minimal introduction to Rust.
categories: [coding, rust]
---
# Flashcard Rust: Result Type in Rust and how to handle it

Rust `Result` is a type used to return / propogate errors from a function to the 
caller. It is an `Enum` with two variants - an `Ok(T)` and an `Err(E)`. 
An `Ok(T)` represents success and error represents failure.


<figure align="center">
<img src="https://i.imgur.com/lxPnX5U.jpg" alt="Result type holds two variants"/>
<figcaption>Rust Result Type</figcaption>
</figure>

In code it looks like:

```rust
enum Result<T, E> {
  Ok(T),
  Err(E),
}
```

Let's use a simple program to see how Result type can be used and handled.
The program below has two functions, an `is_even` and the `main`  function:

```rust
// a simple program that shows how to use Result Type in Rust
use std::io::stdin;

// check if a number is even or odd
// return a Result type (Ok(String) if even, Err(String) if odd)
fn is_even(n: u32) -> Result<String, String> {
    let even = n % 2;
    match even {
        0 => Ok(format!("{} is even!", n)),
        _ => Err(format!("{} is not even!", n)),
    }
}

fn main() {
    // read input from stdin
    let mut input = String::new();
    println!("enter an integer: ");
    stdin().read_line(&mut input).expect("enter an integer!");

    // parse String as u32, returns a Result type
    let input = input.trim().parse::<u32>().unwrap();

    // is_even function returns a custom Result type
    let res = is_even(input).unwrap();
    println!("{:?}", res);
}
```

As the name suggests, `is_even` is used to check if a digit is even or odd, 
it returns a Result Type, both `Ok` and `Err` variants of the type returns
a String in case the digit is even or failure (Error) if its odd.

Let's see how the program works, building and running the program using `cargo`:

```python
➜  results git:(master) ✗ cargo build && cargo run
enter an integer:
2
"2 is even!"
➜  results git:(master) ✗
```

That worked as expected, we gave `2` and it printed on the screen `2 is even`.

Now if we give an odd number, let's see what happens:

```python
➜  results git:(master) ✗ cargo build && cargo run
enter an integer:
1
thread 'main' panicked at 'called `Result::unwrap()` on an `Err` value: "1 is not even!"', src/main.rs:24:30
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

The program panicked with an Error value, `"1 is not even!"`. That is not great, 
error handling to say the least.


The `main` function has a few other things going on as well, the line:

```rust
stdin().read_line(&mut input).expect("enter an integer");
```

tries to read a line of input from standard input as a String  owned by the variable `input`,
if it fails, the program panics and outputs, "enter an integer".

The line: 

```rust
let input = input.trim().parse::<u32>().expect("error in parsing input");
```

trims the input string and tries to parse the value as an unsigned integer, 
it uses the same variable `input` to assign its result, this is called
`shadowing` in Rust, if you are not familar with it, please [see](https://rahul.onl/coding/2020/03/16/vars.html)

Now that you understand the program, let's talk about the ways to handle a 
Result type. There are three ways in general to handle a Result type:

1. `unwrap` - This is the simplest case, here it essentially means, we don't
care about the error, and tells the program to try to get the success (`Ok`) value
and if the call results in  a failure (`Err`), panic. This is okay in the case
we are writing simple scripts, or knows for sure that there should be an `Ok` value,
or if we, you know are lazy.

2. `?` - It is a short hand notation in Rust, which basically tries to unwrap
a value if it's a success (`Ok`) or if it's a failure returns an `Err`. As it can
have two possible variants, and `errors` have to be handled some way, `?`
can only be used inside functions that returns a  Result Type.

We could use it in our program, but we will have to change the  signature of our `main` to:

```rust
fn main() -> Result(<(), std:io:Error> {

    //same code till `let res = ` as original program
    let res = is_even(input)?; // change unwrap to ?
    Ok(())
}
```
This can be read as if failure, main will exit with an error code, if not main
returns nothing a `()`.

3. Finally, we come to the most exhaustive way to handle Result type, here,
we use a `match` express for both success (`Ok`) and failure (`Err`), to capture
and handle all possible scenarios gracefully.

To use it in our original program, remove `is_even(input).unwrap();` line and add:

```rust
fn main() {

    //same code till `let res = ` as original program
    match is_even(input) {
    	Ok(val) => println!("{:?}, val),
	Err(err) => println!("{:?}, err),
    }
}
```

Doing this, we can avoid our program from panicking and now when we run the program,
it doesn't panic:

```python
➜  results git:(master) ✗ cargo build && cargo run
enter an integer:
1
"1 is not even!"
➜  results git:(master) ✗ cargo build && cargo run
enter an integer:
2
"2 is even!"
➜  results git:(master) ✗
```

yay!, now isn't this much better than before :) .

So to wrap up, Result type in Rust is an Enum used to handle success and failure 
scenarios in functions. It can be handled in three ways, using `unwrap`,
using a `?` or using a `match` expression.

## References

For more details, please read:

[Rust docs on Result type](https://doc.rust-lang.org/std/result/index.html)<br/>
[Unwrap and Expect in Rust](https://jakedawkins.com/2020-04-16-unwrap-expect-rust/)<br/>
[Unrwap and Expect](https://learning-rust.github.io/docs/e4.unwrap_and_expect.html)


## The end

In this post, we got a basic idea of what Results are and how to handle them.
Next time, we can see how to handle errors in a bit more detail.

