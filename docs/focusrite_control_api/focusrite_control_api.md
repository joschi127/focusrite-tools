# Focusrite Control API

## Dumped files

In the files

- [client-details.xml](xml/scarlett-18i8-2nd-gen/client-details.xml)
- [device-arrival.xml](xml/scarlett-18i8-2nd-gen/device-arrival.xml)
- [set.xml](xml/scarlett-18i8-2nd-gen/set.xml)

you can find a dump of the XML data that Focusrite Control Server sends to us, after sending a handshake and a keepalive
request.

For details, also see `focusrite_send_test.py`, which we used to send the handshake and keepalive requests.

The handshake request will give us the `device-arrival` response, while the keepalive request will give us the `set`
response with the current state of the device.


## How to read available device options from handshake response

In [device-arrival.xml](xml/scarlett-18i8-2nd-gen/device-arrival.xml) you can find a list of available options which
we can use to control the device.

In [set.xml](xml/scarlett-18i8-2nd-gen/set.xml) we can find the full state dump with the current values for all the
available options.

For example, within `device-arrival.xml` we can find the definition of the `Analogue 1` input which looks like this:

        <analogue id="795" supports-talkback="false" hidden="false" name="Analogue 1" stereo-name="Analogue 1-2">
            <available id="797"/>
            <meter id="798"/>
            <nickname id="796"/>
            <mode id="799">
                <enum value="Line"/>
                <enum value="Inst"/>
            </mode>
            <pad id="800"/>
        </analogue>

It tells us that:
- The `id` for the meter of `Analogue 1` input is `798`. 
- The `id` for the mode switch of `Analogue 1` is `799` and it can be set to `Line` or `Inst`.

And within `set.xml` we can find the current values for these options:

        <item id="798" value="-51.417"/>
        <item id="799" value="Line"/>

So this tells us that:
- The meter of `Analogue 1` is set to `-51.417` dB.
- The mode switch of `Analogue 1` is set to `Line`

Within `device-arrival.xml` we can also find the mixes matrix, which is a list of all the mixes and their inputs:

        <mixes>
            <mix id="54" name="Mix A" stereo-name="Mix A">
                <meter id="127"/>
                <input>
                    <gain id="55"/>
                    <pan id="56"/>
                    <mute id="57"/>
                    <solo id="58"/>
                </input>
                <!-- ... -->
            </mix>
            <!-- ... -->
        </mixes>

And like for the inputs itself, in `set.xml` we can find the current values for these options:

    <item id="55" value="0"/>

And it tells us that:
- The gain of `Mix A` input 1 is currewntly set to `0` dB.


## Important Note on Server Communication & Connection Resets

The Focusrite Control Server can be sensitive to protocol state and command targets. While some invalid commands might
be ignored, others can cause the server to instantly close the connection, resulting in a `Connection reset by peer`
error.

Common pitfalls and behaviors:
1. **Incorrect Protocol Framing:** Commands MUST be **prefixed** (not suffixed) with `Length=XXXXXX ` where `XXXXXX`
    is the byte length of the XML payload encoded as a **6-digit, zero-padded, UPPERCASE HEXADECIMAL** number,
    followed by a single space and then the XML payload. There is **no trailing `\n`** character. For example a
    42-byte payload is framed as `Length=00002A <device-subscribe devid="1" subscribe="true"/>`.
2. **Missing / incomplete Device Subscription:** Before the server accepts and applies any `<set>` command for a
    device, the client MUST first subscribe to that device. The subscribe element **requires the
    `subscribe="true"` attribute**: `<device-subscribe devid="N" subscribe="true"/>`. A bare
    `<device-subscribe devid="N"/>` (without `subscribe="true"`) does **not** establish a real subscription, so the
    server **silently ignores** every subsequent `<set>` command - which is why our earlier write attempts appeared
    to have no effect. (Confirmed against the authentic reverse-engineered client
    `raduvarga/Focusrite-Midi-Control`, `TCPListener.swift`.)
3. **`<set>` command syntax:** The syntax `<set devid="N"><item id="X" value="V"/></set>` is correct. There is no
    separate `<setvalue>` (or similar) command - the server's own full state dump (`set.xml`) uses the very same
    `<item id="X" value="V"/>` elements, so writing a value simply mirrors how the server reports it back.
4. **Client approval / authorisation (the real blocker):** This is what actually prevented our `<set>` commands
    from taking effect. After the handshake the server returns an `<approval>` element, e.g.
    `<approval hostname="focusrite-tools" id="..." type="response" authorised="false"/>`. As long as the handshake
    returns `authorised="false"`,    the server happily accepts the connection, returns the full state dump and accepts
    the subscription, but it **silently ignores every `<set>` command**. The client must first be **approved/trusted
    by the user inside the Focusrite Control desktop application** (the new remote client shows up there and must be
    allowed). The approval is bound to the `client-key` you send in `<client-details .. client-key="..."/>`, so keep
    that key stable -  you only need to approve once; changing the key forces a re-approval. Once `authorised="true"`,
    the very same `<set>` commands take effect immediately. (Verified live against a real Scarlett 18i8 server: framing,
    the `subscribe="true"` subscription and the `<set>`/`<item>` syntax were all already correct - the values only
    stayed unchanged because the response reported `authorised="false"`.)
5. **Higher delay/timeout might be rewuired for loading one of the built-in routing presets.


### How to Control Input Volume (Gain)

The `<analogue>` element in `device-arrival.xml` only exposes hardware-input controls such as `<meter>`, `<mode>` and
`<pad>` - it does **not** contain a gain element, because the per-input level is controlled inside the mixer matrix.
The actual volume/gain control for a mixer input is found within the `<mixer>` -> `<mixes>` section.

For example, in `Mix A` (id `54`), you can find the gain control for the first input:

        <mix id="54" name="Mix A" stereo-name="Mix A">
            <input>
                <gain id="55"/>
                <pan id="56"/>
                <mute id="57"/>
                <solo id="58"/>
            </input>
        </mix>

So to set the gain of `Mix A` input 1 to -10 dB, we send the following XML payload (using the correct framing and
**after** having subscribed to the device via `<device-subscribe devid="1" subscribe="true"/>`):

        <set devid="1"><item id="55" value="-10.0"/></set>

The target id (`55`) and the `<set>`/`<item>` syntax were correct all along. A live test against a real Scarlett
18i8 server finally revealed the true reason earlier `<set>` commands had no effect: the server responded with
`authorised="false"`, meaning this client had not been approved in the Focusrite Control desktop application (see
point 4 above). While unapproved, the server silently ignores every `<set>`. After approving the client (and keeping
the same `client-key`), the identical command above changes the value as expected.


### How to Switch the Input Mode (Line / Inst)

Some analogue inputs can be switched between `Line` and `Inst(rument)` mode. These inputs expose a `<mode>` element
in `device-arrival.xml`, which lists the selectable values as `<enum>` entries. For `Analogue 1` (input id `795`) the
mode control is defined with id `799`:

        <analogue id="795" supports-talkback="false" hidden="false" name="Analogue 1" stereo-name="Analogue 1-2">
            <available id="797"/>
            <meter id="798"/>
            <nickname id="796"/>
            <mode id="799">
                <enum value="Line"/>
                <enum value="Inst"/>
            </mode>
            <pad id="800"/>
        </analogue>

To switch the input mode, send a `<set>` for the `<mode>` id using one of the `<enum value="..."/>` names exactly as
listed above. For example, to switch `Analogue 1` to instrument mode:

        <set devid="1"><item id="799" value="Inst"/></set>

To switch it back to line level, send `value="Line"` instead:

        <set devid="1"><item id="799" value="Line"/></set>

Only the inputs that actually contain a `<mode>` element support this switch (on the Scarlett 18i8 2nd Gen these are
`Analogue 1` with id `799` and `Analogue 2` with id `805`). The same framing,
`<device-subscribe devid="1" subscribe="true"/>` subscription and client approval requirements described above apply
here as well.


### How to Switch the Routing Profile (Preset)

The device exposes its built-in routing presets through the `<preset>` element in `device-arrival.xml`. For the
Scarlett 18i8 (2nd Gen) it is defined with id `6` and lists the selectable preset names as `<enum>` values:

        <preset id="6">
            <enum value="Direct Routing"/>
            <enum value="System Playback"/>
            <enum value="2 Channel Analogue"/>
            <enum value="8 Channel Analogue"/>
            <enum value="Digital"/>
            <enum value="Analogue + Digital"/>
            <enum value="Empty"/>
        </preset>

To switch the active routing profile, send a `<set>` for id `6` using one of the `<enum value="..."/>` names exactly
as listed above. For example, to load the `8 Channel Analogue` preset:

        <set devid="1"><item id="6" value="8 Channel Analogue"/></set>

Please note: For some reason the current value of `id="6"` is not reported in the full state dump (`set.xml`).

The same framing, `<device-subscribe devid="1" subscribe="true"/>` subscription and client approval requirements
described above apply here as well.
