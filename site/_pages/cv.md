---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

[**Download my CV (PDF)**]({{ base_path }}/files/CV.pdf){: .btn .btn--primary}

Education
======
* Add your degrees here.

Work experience
======
* Add your roles here.

Skills
======
* Add your skills here.

Publications
======
  <ul>{% for post in site.publications reversed %}
    {% include archive-single-cv.html %}
  {% endfor %}</ul>
