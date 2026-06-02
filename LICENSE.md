# CBL — Single-Site License Agreement

**IMPORTANT — READ BEFORE USING.** By installing, deploying, or using this
software ("the Software"), you ("the Licensee") agree to the terms below. If you
do not agree, do not use the Software and request a refund per the marketplace's
policy.

This is a license, not a sale. The Software is licensed, not sold.

---

## 1. Grant of license

Upon purchase, you are granted a non-exclusive, non-transferable license to
install and operate the Software for **one (1) live production website / domain
per license purchased** (the "Licensed Site").

You may also run additional **non-public** copies (local development, staging,
or testing) that support that one Licensed Site.

## 2. What you may do

- Deploy the Licensed Site to a host of your choice.
- Modify the source code for your own use on the Licensed Site.
- Use it for a personal or commercial website.

## 3. What you may not do

- Operate more than one public/production site from a single license. Each
  additional public site requires an additional purchased license.
- Resell, redistribute, sublicense, share, or publish the Software or its source
  code, in original or modified form, to any third party.
- Use the Software to build sites for multiple clients under one license (one
  license = one site; agency/multi-site licensing is available separately).
- Remove, disable, or circumvent the license validation described in Section 5
  while operating the Software, or misrepresent your license status.

## 4. Ownership

All rights, title, and intellectual property in the Software remain with the
author. This license grants use rights only.

## 5. License validation & telemetry (please read)

To enforce the one-site limit and detect license abuse, the Software performs a
periodic, lightweight "license check": at most once per day, the running site
sends the following to the author's license server:

- your license key,
- the site's domain/hostname,
- an anonymous install identifier (a random ID),
- the site name and software version.

**It does not collect or transmit your visitors' data, your customers' personal
information, your content, or any database contents.** It is used solely to
validate your license and identify use of one license across multiple sites.

This check is **report-only** — it does not disable or interfere with your site.
You may inspect exactly what is sent in `core/licensing.py`. License validation
can be configured via the `LICENSE_*` environment variables (see the README);
operating the Software with validation disabled, or without a valid license key,
is a breach of this Agreement.

## 6. Updates

Updates, if provided, are delivered through the marketplace and are licensed
under these same terms.

## 7. No warranty

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.

## 8. Limitation of liability

IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM,
OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 9. Termination

This license terminates automatically if you breach any term. On termination you
must stop using and delete all copies of the Software.

---

© <2026> <CBL>. All rights reserved.
Questions about licensing (including agency / multi-site licenses): <codewithmichael26@gmail.com>.
