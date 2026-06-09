# Focusrite Control API

## Dumped files

In the files
- [client-details.xml](xml/scarlett-18i8-2nd-gen/client-details.xml)
- [device-arrival.xml](xml/scarlett-18i8-2nd-gen/device-arrival.xml)
- [set.xml](xml/scarlett-18i8-2nd-gen/set.xml)
you can find a dump of the XML data that Focusrite Control Server sends to us, after sending a handshake and a keepalive
request.

For details, also see `focusrite_send_test.py`, which we used to send the handshake and keepalive requests.


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


## Important Note on Server Communication & Connection Resets

The Focusrite Control Server is extremely sensitive to protocol state and command targets. If it receives a command it
doesn't like or if the command is sent at the wrong time (e.g., before the initial state dump is finished), it will
instantly close the connection, resulting in a `Connection reset by peer` error.

Common causes for connection resets:
1. **Targeting Read-Only Options:** Some options, such as `<meter>` elements (e.g., id `798`), are status indicators and
   cannot be modified.
2. **Incorrect XML Format:** Ensure the XML is properly wrapped (usually in `<set devid="1">...</set>`) and ends with a
   `\n` character.
3. **Protocol Synchronization:** Always wait for the initial `device-arrival` and `set` (full state) dumps after the
   handshake before sending your first `<set>` command.


### How to Control Input Volume (Gain)

While the `<analogue>` element in `device-arrival.xml` might only show a `<meter>` and `<mode>`, the actual volume/gain
control for an input is typically found within the `<mixer>` -> `<mixes>` section. 

For example, in `Mix A` (id `54`), you can find the gain control for the first input:

        <mix id="54" name="Mix A" stereo-name="Mix A">
            <input>
                <gain id="55"/>
                <pan id="56"/>
                <mute id="57"/>
                <solo id="58"/>
            </input>
        </mix>

So to set the gain for this input to -10dB, we have to send the following XML to the Focusrite Control Server:

        <set devid="1"><item id="55" value="-10.0"/></set>
