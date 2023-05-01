# napari metadata plugin testing

Author: Lucy Obus (@lcobus)

Date: 2023, May


## Summary

- CZI Imaging Tech was motivated to help improve the way napari handles layer metadata, with particular interest in essential metadata attributes like axis names and units that can be critical for accurate processing and visualization of biological data.
- Andy Sweet decided to see how much improvement could be made by contributing a napari plugin that uses and augments the existing napari public API.
- To support engineering effort, a targeted concept testing study of the prototype was run by @lcobus with support from @chili-chiu to evaluate plugin feature intuitiveness, overall user value, and learn from participants about the tradeoffs between application as a plugin vs contributing to core napari.
- We spoke with several community members including @JoOkuma @ziw-liu @toloudis , with the goal of hearing from a diversity of voices that include the OME, AICSIO, napari core developer, and iohub communities. We also did internal testing with CZI application scientists prior to external testing.
- During the session, we asked participants to describe their current data complexities and metadata needs, issues, and tools, before asking them to share their screen, use the plugin on their data, and provide feedback.
- Participants validated prototype value, both as an individual to spot check and adjust info, and even moreso as a tool to use with collaborators to save time and effort. They also offered specific feedback on design/layout choices, which has been noted for future iterations.
- The biggest area for continued discussion is whether metadata should stay as a plugin or contribute upstream.


## Goals

1. Evaluate intuitiveness to recommend small changes that improve user experience and functionality
2. Validate current user value to determine if plugin should be released/completed
3. Explore long term strategic tradeoffs of functionality as a plugin vs upstream contributions to support product decision on contribution effort.


## Who we tested with

- Initial internal testing: Application Science team revealed several interaction and clarification improvements.
- External 6 participants focused on diversity of communities with vested interest in metadata standards from developer POV: OME, AICSIO, iohubnapari core developers, iohub.
- Additional informal testing and discussions ongoing throughout prototype build.


## Metadata handling as is

- 3 metadata utilizations: individual interaction, collaborative/supportive interaction with a non-developer colleague, utilization for other plugins they build.
- File size ranges from 100 gigabytes to several terabytes, from individual stack slices to instances that can’t be supported in memory. Complexity ranges: 3D+Time, up to 6D.
- Major challenges with current metadata: non standardized and/or custom formats and conversion across several tools from acquisition to analysis result in metadata loss, labor of adding in additional manual metadata (like timeseries), confusion about what is important to keep.
- Related quotes:
    * *“It’s this horrible, unsolved problem - what is the standard, what is important, what is not? One process we do is read a file in one format then marry it to another metadata standard, and strive for completeness. We generally go from proprietary to general."*
    * *“My goal is to move to iohub and let that take care of the metadata.”*
    * *“I avoid the metadata conversation- there are lots of good solutions, no perfect solutions. I’m more than happy to adjust my work to meet whatever community standard.”*


## Learning goal 1: plugin user experience & functionality

- Participants identified and were satisfied with key job stories implemented (axes/ruler/scale, editing capability).
- Participants noted clean, responsive design that “looks like most napari dock widgets, and make sense spatially”.
- Several participants questioned the units dropdown, if the offerings were sufficient for unit needs.
- “Save” functionality confused participants, requires clarity on what/where it is saving.
    - *“It scared me - I need clarity on whether it's saving to file or layer.”*
    - *“It seems out of scope for a plugin to save beyond the layer, but because i’m working with thousands of images, it’s unlikely I’d be editing/saving individual images.”*
    - *“This is super tricky, saving to file is always gonna be tricky, you risk clobbering someone else’s work.”*

**Recommendations**

- Indicator when data is empty because it doesn’t exist, or empty because data couldn’t be pulled
- Rethink large empty space
- Consider updating “view full metadata” to button
- Add additional metadata to “view full metadata” section, akin to json file or collapsible AICSIO plugin


## Learning goal 2: validate current user value

- We asked participants to rank the value of this plugin to their work today, as well as to sharing with collaborators, with 5 being “this would be invaluable today” and 1 being “this would provide no value whatsoever.”
    - **For individual value, participants averaged a ranking of 3.** While users of console or prestep metadata tools, participants identified strong value add of a widget metadata experience to rename axes to align across data sets, semantic labeling to understand how to process images, change scale to expected values, and view full metadata for context
        - *“It’s nice to visually and interactively confirm this metadata.”*
        - *“I don't necessarily always want to look at it, but if it isn't there, I feel like it's missing.”*
    - **For collaborator value, participants averaged a ranking of 4.2.** As developers, participants acknowledged they could perform much of this functionality in console, but sharing this functionality with collaborators would save time and effort.
        - *“It's a much more comfortable experience for them.”*
        - *“While I might make a lot of these changes in console, I would love to give this to a colleague and tell them to adjust the transform in GUI. This would be really useful for collaboration.”*


### Learning goal 3: explore long term functionality as plugin vs upstream contribution

- non-napari core developers believed the functionality should live in core napari viewer, to make it easier to develop other plugins that would rely on this data, and to identify standards
    - *“I really want something upstream, now there is no way to tell standards. Napari is the de facto standard image viewer for python; if napari did it we would all be happy.”*
    - *“I’d prefer to have it in core napari, because it would be easier to develop plugins that rely on the axes names. If it was in core tomorrow, my reader would set these automatically.”*
    - *“Shouldn’t this be basic functionality? Do plugins graduate to core?”*

- napari core developers said it should be a plugin bundled with core napari like the console
    - *“It’s nice to have separation. Longer term, my hope is that there’s a nice interface for these types of metadata in napari. We should make an interface that allows users to adapt names.”*
    - *“I want it to be integrated into core napari but stay a dock widget.”*
