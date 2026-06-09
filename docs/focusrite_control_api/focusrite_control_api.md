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

In [set.xml](xml/scarlett-18i8-2nd-gen/set.xml) we can find the current values for all available options.

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
- The `id` for the meter of `Analogue 1` input is `798`. It can be set to 
- The `id` for the mode switch of `Analogue 1` is `799` and it can be set to `Line` or `Inst`.

And within `set.xml` we can find the current values for these options:

        <item id="798" value="-51.417"/>
        <item id="799" value="Line"/>

So this tells us that:
- The meter of `Analogue 1` is set to `-51.417` dB.
- The mode switch of `Analogue 1` is set to `Line`
