# PikiBot NonCommercial License 1.1.0

Copyright (c) [YEAR] DA-344. All rights reserved except as granted below.

## Important Notice

This license is an independently authored work inspired by the structure and concepts of the PolyForm
Noncommercial License 1.0.0. It is not an official PolyForm license, and it is not affiliated with,
sponsored by, or endorsed by the PolyForm Project.

This is a **source-available** license. It is **not** an open-source license as defined by the Open Source
Initiative, because it restricts Commercial Use. The Original Software is public, but it is not free of
restrictions.

## 1. Acceptance

By exercising any right granted under this License (including the rights to use, copy, modify, or
distribute the Original Software), You accept and agree to be bound by this License. If You do not agree,
You may not exercise any right granted by it.

## 2. Copyright License

Subject to this License, the Licensor grants You a worldwide, non-exclusive, royalty-free,
non-transferable, non-sublicensable (except as stated in this License) license to use, reproduce, modify,
and distribute the Original Software for Noncommercial Purposes only.

This grant applies only to the Original Software. It does not grant any right to use, reproduce, modify,
or distribute the Original Software for Commercial Use.

The Licensor retains all rights, title, and interest in the Original Software, except for the rights
expressly granted by this License.

## 3. Distribution

You may distribute the Original Software, including Modified Versions, for Noncommercial Purposes. When You
do, You must:

1. provide a copy of this License, or a clear reference to its canonical version;
2. retain all copyright, license, and attribution notices in the Original Software;
3. include a Notice that lists the files of the Original Software that have been modified, added, or
   removed, and clearly indicates Your modifications;
4. include, as part of that Notice, the API Additions Statement described in Section 8.4, if Your Modified
   Version changes the API Surface in any way; and
5. not represent the Original Software, Your Modified Version, or its author as officially affiliated with,
   endorsed by, or supported by the Licensor unless the Licensor has expressly authorized it in writing.

You may not distribute the Original Software or any Modified Version for Commercial Use under this License.

## 4. Notices

You must retain all notices included in the Original Software and, when distributing, provide the notices
required by this License in a reasonably accessible location (for example, a file named `NOTICE` or
`LICENSE`). Notices must not be altered or removed in a way that hides or misrepresents authorship,
copyright, licensing terms, or modification history. The Notice required by Section 3 may be placed in the
same file.

## 5. Modifications and New Works

You may modify the Original Software and create works based on it for Noncommercial Purposes.

1. Copyright in material You independently create remains Yours.
2. Creating a modification or new work does not transfer, alter, or end the Licensor's rights in the
   Original Software.
3. Any Original Software contained in, or from which a work is derived, remains subject to this License.
4. Your Independent Contributions may be licensed under terms of Your choice (open-source, source-available,
   noncommercial, or proprietary), as long as that license does not grant rights to the Original Software
   beyond those granted by this License.
5. Independent Contributions may be used commercially only to the extent You have the right to do so under
   their own license, **and** only if that use does not constitute Commercial Use of the Original Software.

## 6. Commercial Use

"Commercial Use" means any use of the Original Software that is primarily intended for, or directed toward,
commercial advantage, monetary compensation, or revenue generated from the Original Software or its
functionality. It includes, without limitation:

1. selling, licensing, sublicensing, or otherwise providing the Original Software for compensation;
2. offering the Original Software, or functionality of it, as part of a paid product, service,
   subscription, or membership;
3. offering the Original Software, or functionality of it, as a service to third parties for compensation
   (including hosting it for others);
4. charging for, or otherwise monetizing, functionality of the Original Software;
5. placing the Original Software, or functionality of it, behind a paywall, subscription, entitlement, or
   other commercial access restriction; and
6. any other use aimed at obtaining commercial advantage or compensation from the Original Software or its
   functionality, **including by indirect means described in Section 8.3**.

The use of the Original Software by a company or other commercial entity is not, by itself, Commercial Use,
as long as it does not commercially exploit the Original Software or its functionality.

## 7. Noncommercial Purposes and Organizations

"Noncommercial Purposes" means purposes that do not constitute Commercial Use. They include, without
limitation: personal use; education (teaching, learning, coursework, academic projects); research and
experimentation; development and testing; evaluation and demonstration; and modification or customization
for personal or organizational use, provided it is not Commercial Use.

A person or organization does not lose the ability to act for Noncommercial Purposes just because it carries
out commercial activities, as long as the use of the Original Software itself is not Commercial Use. In
particular, an organization is not making Commercial Use solely because it operates commercially, earns
revenue from unrelated activities, uses the Original Software internally, or uses it for development,
testing, research, or evaluation.

You may run the Original Software on personal or privately controlled servers, and share it or Your
modifications with other individuals for Noncommercial Purposes, subject to Section 3.

## 8. Public API and API Boundary

### 8.1 The Public API is limited and separately licensed

The Public API is governed by a separate license (the "API License"), identified by the Licensor in the
Original Software (for example in a file named `API_LICENSE` or in the API Manifest). The API License grants
rights only to the Public API itself and to nothing else.

The Public API consists **only** of the interfaces, functions, classes, definitions, and documentation that
the Licensor has expressly listed as public in the API Manifest of the Original Software, as published by
the Licensor. Anything not so listed is **not** part of the Public API, including the `Core` and `Modules`
directories and all internal or private interfaces.

### 8.2 What You may do with the Public API

You may use the Public API to develop, distribute, license, and commercially provide Plugins and
Independent Software that interact with the Original Software, subject to the API License. Independent code
that only uses the Public API and does not include, incorporate, or constitute Original Software remains
under the license chosen by its author.

### 8.3 API Boundary and anti-circumvention

The API Surface is fixed by the Licensor, not by third parties. Accordingly:

1. Exposing, wrapping, forwarding, re-exporting, proxying, or otherwise making Original Software
   functionality reachable through an API does **not** make that functionality, or the Original Software it
   comes from, part of the Public API or subject to the API License.
2. A Modified Version, fork, or derivative work (a "Fork") that adds, widens, or reclassifies API Surface
   so as to expose functionality from `Core`, `Modules`, or any other part of the Original Software that is
   not already in the Public API is not covered by the API License with respect to that functionality.
   Using such API Surface to offer that functionality for Commercial Use is Commercial Use of the Original
   Software and is prohibited.
3. Nothing in this License allows You to use a Plugin, an Independent Contribution, the Public API, a Fork,
   or any intermediary layer as a means of circumventing the restrictions that apply to the Original
   Software. Acts done for that purpose, or having that effect, are treated as done directly.
4. A Fork may add API Surface only if it is one of the following (an "Allowed API Addition"):
   1. **New to the Fork:** the exposed functionality is an Independent Contribution that is original to the
      Fork and contains no Original Software beyond what this License permits; or
   2. **Strictly Necessary:** the addition is strictly necessary for an Independent Contribution of the Fork
      to interoperate with the Original Software, meaning that (a) the interoperability cannot reasonably be
      achieved through the existing Public API, (b) the addition is limited to the minimum surface needed,
      and (c) it does not, in substance, make the Original Software's functionality available for Commercial
      Use.
5. Allowed API Additions remain subject to this License to the extent they expose or contain Original
   Software. They do not extend the Public API or the API License to any other part of the Original
   Software.

### 8.4 API Additions Statement

A Fork that is distributed and that adds or changes API Surface must include in its Notice an "API
Additions Statement" that lists each added or changed API element and states which exception in Section 8.3
(4) applies to it, with a brief justification. If the statement is missing, the additions are presumed not
to be Allowed API Additions until You show otherwise.

### 8.5 Licensor's authority over the Public API

Only the Licensor may expand or reduce the Public API, by updating the API Manifest. A change by the
Licensor applies from the version in which it is published and does not affect rights already granted.

## 9. Plugins and Independent Contributions

Plugins and Independent Contributions are works created by You or another author that extend, interact with,
or integrate with the Original Software without being, or containing, the Original Software.

1. You keep all rights in Your Plugins and Independent Contributions, subject to the rights that apply to
   any Original Software they contain.
2. You may license, sell, or commercially provide them (including through paid services, subscriptions,
   memberships, Discord SKUs, or entitlements), provided the commercial use is limited to the Plugin or
   Independent Contribution and is not Commercial Use of the Original Software.
3. A work does not become Original Software merely because it depends on, communicates with, or is
   distributed together with the Original Software.
4. Where a Plugin or Independent Contribution contains or is derived from Original Software, that portion
   stays under this License.
5. Section 8.3 prevails over this Section if the two conflict.

## 10. Patent License

Subject to this License, the Licensor grants You a worldwide, non-exclusive, royalty-free patent license to
make, have made, use, offer to sell, import, and otherwise transfer the Original Software, only to the
extent needed to exercise the rights expressly granted by this License, and only for patent claims owned or
controlled by the Licensor that are necessarily infringed by the Original Software, alone or in a
combination reasonably contemplated by the Licensor.

No patent license is granted for modifications, Independent Contributions, Plugins, other combinations, or
any claim not necessarily infringed by the Original Software. No trademark license is granted.

If You start patent litigation against the Licensor or anyone else alleging that the Original Software
infringes a patent, the patent license in this Section ends on the date the litigation starts.

## 11. Fair Use and Mandatory Law

Nothing in this License limits any right You have under applicable law independently of this License
(including fair use, fair dealing, or other statutory exceptions), and nothing in it expands any such
exception. Nothing in this License excludes or limits any right or liability that cannot lawfully be
excluded or limited.

## 12. No Other Rights

Except for the rights expressly granted, no other rights or licenses are granted, whether by implication,
estoppel, exhaustion, or otherwise. In particular, this License does not grant rights to the names, logos,
or branding of the Licensor or of PikiBot, to any patent except as stated in Section 10, or to any
third-party material included with or distributed alongside the Original Software, which remains under its
own license. The Licensor has no obligation to provide source code, documentation, support, or updates
beyond what it chooses to make available.

## 13. No Indemnity

The Licensor has no obligation to defend, indemnify, or hold You harmless against any claim that the
Original Software or Your use of it infringes any right of a third party. You are solely responsible for
claims arising from Your use, modification, or distribution, including modifications, combinations,
Independent Contributions, and Plugins. The Licensor may, but need not, take part in any defense.

## 14. Termination and Cure

Your rights under this License end automatically if You materially violate it.

If You stop the violation and cure it within thirty (30) days after You become aware of it, or after the
Licensor gives You written notice of it (whichever happens first), Your rights are automatically
reinstated. Rights terminated permanently are not reinstated for anyone who has received notice of the
violation and continues to violate this License.

Upon termination You must stop exercising the rights granted and, where reasonably practicable, stop
distributing the Original Software and Modified Versions. Termination does not affect licenses You obtained
independently (for example the API License or the license of an Independent Contribution), and does not
limit any other remedy available to the Licensor.

## 15. Versioning

The Licensor may publish new versions of this License, each with its own version number. A change to
substantive terms (permissions, restrictions, definitions, or obligations) requires a new version number.
Purely editorial changes (typos, formatting, broken references) do not change the version and may be
identified by an updated revision number and date.

1. The version that applies to a given copy is the one the Licensor identifies or includes with that copy.
2. A newer version does not affect rights granted under an earlier version, and does not apply to existing
   copies unless they are expressly released or relicensed under it.
3. Forks and distributions must identify the version under which the Original Software is distributed and
   must not present another version as applying to rights already granted.
4. You are not required to accept a newer version, and declining it does not terminate rights granted under
   the earlier one, except where this License or applicable law allows termination.

## 16. Disclaimer of Warranty and Limitation of Liability

THE ORIGINAL SOFTWARE IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
EXPRESS, IMPLIED, STATUTORY, OR OTHERWISE, TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW. THE LICENSOR
DISCLAIMS ALL WARRANTIES, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE,
NON-INFRINGEMENT, AND ANY ARISING FROM COURSE OF DEALING, USAGE, OR TRADE PRACTICE. THE LICENSOR DOES NOT
WARRANT THAT THE ORIGINAL SOFTWARE WILL MEET YOUR REQUIREMENTS, OPERATE WITHOUT INTERRUPTION, BE SECURE OR
ERROR-FREE, OR BE FREE OF HARMFUL COMPONENTS.

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE LICENSOR WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR OTHER DAMAGES ARISING OUT OF OR RELATING TO THE USE OF, OR
INABILITY TO USE, THE ORIGINAL SOFTWARE, INCLUDING LOSS OF DATA, PROFITS, REVENUE, OR BUSINESS, UNDER ANY
LEGAL THEORY (CONTRACT, TORT, NEGLIGENCE, STRICT LIABILITY, OR OTHERWISE), EVEN IF ADVISED OF THE POSSIBILITY
OF SUCH DAMAGES.

## 17. Severability and Interpretation

If any provision of this License is held unenforceable, it will be applied to the maximum extent permitted
and the rest of this License remains in effect. Headings are for convenience only. "Including" and
"includes" mean "including without limitation". Where this License refers to the Licensor's identification
or designation of anything (components, API Manifest, API License), that identification is made in writing
in the Original Software or at the canonical license location.

## 18. Derivative Licenses

Anyone may use this License as the basis for a different license. A license that changes the rights or
restrictions of this one must:

1. not use the name "PikiBot NonCommercial License", any confusingly similar name, or any version number of
   this License to identify itself, except to accurately state that it is derived from this License;
2. remove the PikiBot name and any reference that could suggest it is an official PikiBot license;
3. state clearly that it is independently authored, is not the PikiBot NonCommercial License, and is not
   affiliated with, sponsored by, or endorsed by the Licensor or PikiBot; and
4. use its own name, version number, and identification.

Purely editorial corrections do not create a new license. Any substantive change is a new version or a
derivative license and must not be presented as an official revision unless the Licensor expressly
authorizes it. A derivative license creates no affiliation or relationship with this License or the
Licensor.

## 19. Definitions

- **Licensor**: the copyright holder or holders of the Original Software who made it available under this
  License.
- **You**: the individual or legal entity exercising rights under this License. If You act for an entity,
  You represent that You have authority to bind it. The entity gets no rights beyond Yours unless it
  obtains them independently.
- **Original Software**: the software originally released by the Licensor under this License, including the
  Original Components and any other files or materials the Licensor expressly identifies as covered. It does
  not include Independent Contributions, Plugins, the Public API (which is under the API License), or
  third-party material, except to the extent they contain Original Software.
- **Original Components**: the files, directories (including `Core` and `Modules`), modules, and source code
  that the Licensor identifies as original components of PikiBot.
- **Independent Contribution**: original material created by You or another author that is added to,
  extends, modifies, or interacts with the Original Software and does not itself constitute or incorporate
  Original Software. Material copied or derived from Original Software is not an Independent Contribution to
  the extent of the Original Software it contains.
- **Plugin**: an Independent Contribution designed primarily to extend, customize, integrate with, or
  interact with the Original Software, including through the Public API.
- **Independent Software**: software that interacts with the Original Software only through the Public API
  and does not include, incorporate, or constitute Original Software.
- **Public API**: the portion of the Original Software's interfaces expressly listed as public in the API
  Manifest and covered by the API License (see Section 8).
- **API Manifest**: the document or file, published by the Licensor with the Original Software, that lists
  the elements of the Public API.
- **API Surface**: every function, class, method, endpoint, command, event, hook, or other interface through
  which software outside the Original Software can reach or invoke functionality.
- **Modified Version**: a version of the Original Software that has been modified, adapted, translated,
  rearranged, or otherwise changed. A Modified Version stays subject to this License with respect to the
  Original Software it contains or is derived from.
- **Fork**: has the meaning given in Section 8.3 (2).
- **Commercial Use**: has the meaning given in Section 6.
- **Noncommercial Purposes**: has the meaning given in Section 7.
- **Distribution**: making the Original Software, a Modified Version, or a work containing Original Software
  available to another person or entity (copies, publication, hosting for download, repositories, package
  registries, physical media, or similar). Using the software yourself, without making it available to
  others, is not Distribution.
- **Notice**: the file or section that contains the notices and statements this License requires.

---

**License:** PikiBot NonCommercial License
**Version:** 1.1.0
**Last Modified:** October 26th, 2026
**Revision:** 1