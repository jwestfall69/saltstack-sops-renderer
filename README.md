# Saltstack SOPS Renderer
This is a basic [sops](https://github.com/getsops/sops) renderer for salt.  I didn't see one already out there when googling and was looking for one for my homelab setup.  sops is much more convenient as it lets you directly create/edit the .sls's with encrypted data in them.  There is no need to use an external program to encrypt/decrypt the data then having to cut/paste/format it into the .sls file.

It was written against salt 3006.x

- [Config Options](#config-options)
  * [sops_args: [sops cli args]](#sops-args---sops-cli-args-)
  * [sops_env: [dict of environment key/value pairs]](#sops-env---dict-of-environment-key-value-pairs-)
  * [sops_timeout: [time in seconds]](#sops-timeout---time-in-seconds-)
- [Installation](#installation)
- [Getting salt to use the sops renderer](#getting-salt-to-use-the-sops-renderer-on-an-sls-file-with-sops-encrypted-data-in-it)
- [Quirks](#quirks)
  * [Editing .sls with sops](#editing-sls-with-sops)
  * [Editing sops encrypted .sls outside of sops](#editing-sops-encrypted-sls-outside-of-sops)

## Config Options
sops has a lot of cli options along with environment variables for determining how it should encrypt/decrypt data.  I gave full control of how sops is called via the options below.  These options should be part of the salt masters config, for my setup I put them in `/etc/salt/master.d/sops.conf`.  Refer to the `sops.conf` provided in this repo as an example

### sops_args: [sops cli args]
This option is required and is used to specify what cli options will get used when running sops to decrypt.  Interaction with sops is done over its stdin/stdout, so a minimum you **must** have these options for the renderer to function:<br>
```
sops_args: --output-type=yaml --input-type=yaml -d /dev/stdin
```

### sops_env: [dict of environment key/value pairs]
This option is optional and allows passing in environment variable(s) to sops.  For example, sops only has an environment variable for pointing at an alternate location for your 'age' private key.  I use the following in my setup to do this.

```
sops_env:
  SOPS_AGE_KEY_FILE: /etc/salt/age/key.txt
```
### sops_timeout: [time in seconds]
This option is optional with a default value of 5.  sops can be setup for pulling key info from the network/cloud.  The timeout is to prevent sops from hanging forever waiting if access to the network/cloud is broken.

## Installation
  * sops must be installed on your salt master server.  Refer to the official sops documentation on how to do that along with understanding how to use sops.
  * Copy `sops.py` into the `_renderers` directory of your states tree
  * On your salt master run `salt-run saltutil.sync_renderers saltenv=<saltenv>`
    * This will copy the `sop.py` into the salt master's `extmods/renderers/` cache
  * copy `sops.conf` into your salt master's `/etc/salt/master.d/` directory and modify it to your needs per above
    * This will require a restart of salt-master to pick up the new config (or if you change it later)
  * [optional] Copy the .sops.yaml into the root of your pillar tree and modify to your needs.
    * This file doesn't get used by salt, but by the user(s) creating/editing encrypted .sls files.

## Getting salt to use the sops renderer on an .sls file with sops encrypted data in it
In order for salt to use the sops renderer it requires add `#!sops|yaml` on the first line of the .sls.  For example using sops to create a new file it would looks like this:

```
#!sops|yaml
somekey:
    password: mypass
```

The resulting encrypted file would contain

```
#!sops|yaml
somekey:
    password: ENC[AES256_GCM,data:PUuocE2Q,iv:F5mNFBVeCk1pQBSO+ro4c3nEUVQ3XY+t3p0+d1YfVQ0=,tag:Mx2gnZywVuT77/YOIdZyeg==,type:str]
sops:
...
```

The first line will trigger salt to send the contents of the .sls file to the sop renderer, then the decrypted yaml onto the yaml renderer.

## Quirks
### Editing .sls with sops
sops infers the file type based on the file's extension.  salt uses its own extension of .sls, which sops doesn't know about.  Because of this is necessary to force the in/out file type when running sops

```
$ sops --input-type=yaml --output-type=yaml filename.sls
```
The easiest way around this annoyance is to setup a alias.

```
$ alias salt-sops='sops --input-type=yaml --output-type=yaml'
```

### Editing sops encrypted .sls outside of sops
sops only encrypts the required values within the .sls file.  This will mean keys and possibly other key/value pairs are unencrypted within the file.  You **must** edit a sops encrypted .sls with sops even if you are only changing a non-encrypted part of the file.  sops keeps a mac/hash of all of the data and if it doesn't match up it will refuse to decrypt the file.

```
$ vi test.sls
  ^^ make change to non-encrypted data in test.sls
$ salt-sops test.sls
MAC mismatch. File has B7CE0BA5553D35642387CFB5B4771A62AAD1B0B153EEE4F641830FA6ADAD1138736085814D031291C78A16C454744391D84D41D79A3775663DDD476B0F44FFF7, computed E5B3EE7781D15692B81DDF657910F73DC08343A53FB94A55139E05CC9DAD5B5ECB57566E67B0F4AEE43333B43583F8CAD040DDA541B30E4ACEB27BDF6B89B156
```