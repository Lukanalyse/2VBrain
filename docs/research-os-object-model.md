# Research OS Object Model

Research OS is meant to grow slowly from real research work. It should not start
with demo content, generated examples, or a pre-filled taxonomy. A clean Vault
contains only Obsidian configuration and empty Research OS folders; the useful
structure emerges as you read, extract, connect, and synthesize.

## Paper

A Paper is the canonical record of a source you have read or plan to read. In
practice, this usually starts from an imported PDF and a Markdown note generated
next to it in the Vault.

Create a Paper when a source is important enough that you may cite it, compare
it, revisit it, or extract durable ideas from it. Do not create a Paper for every
web page, quick note, or passing mention. The Paper object should represent a
real research source.

A Paper contains bibliographic metadata, the PDF reference, reading notes, a
summary, limitations, important quotes or equations, and links to Concepts,
Projects, Brainstorms, or Reviews. It evolves from "unread source" to "annotated
source" to "synthesized evidence." The note can stay sparse at first; its value
comes from being linked to the rest of the system.

Papers link most often to Concepts because they provide evidence, definitions,
methods, or counterexamples. They link to Projects when they are directly useful
for an active question, to Brainstorms when they trigger exploratory ideas, and
to Reviews when they become part of a synthesis corpus.

Good practice: keep source-specific claims in the Paper note. Move reusable
ideas into Concept notes only after you have seen that the idea matters beyond a
single source.

## Concept

A Concept is a reusable unit of understanding. It can be a method, theory,
mechanism, metric, problem class, assumption, dataset pattern, or recurring
distinction.

Create a Concept when an idea appears across multiple sources, explains a
pattern, or is likely to be reused in projects and reviews. Avoid creating
Concepts for one-off phrases. A Concept should be stable enough that it can
accumulate evidence over time.

A Concept contains a working definition, boundaries, examples, open questions,
related concepts, and linked Papers. It evolves from a rough definition to a
small knowledge hub. Early Concepts may be provisional; mature Concepts should
explain what the idea is, what it is not, and why it matters.

Concepts are linked to Papers for evidence, to other Concepts for structure, to
Projects for active use, to Brainstorms for exploration, and to Reviews as
themes in a synthesis.

Good practice: keep Concepts small and composable. If a Concept becomes a long
essay with many subtopics, split it into narrower Concepts and link them.

## Project

A Project is an active research objective. It represents something you are trying
to produce or decide: an experiment, paper section, thesis chapter, product
feature, research question, or implementation plan.

Create a Project when there is a concrete outcome, decision, or deliverable. Do
not use Projects as general topic folders; use Concepts for reusable knowledge
and Reviews for synthesis.

A Project contains the goal, context, current state, decisions, tasks, relevant
Papers, useful Concepts, and open risks. It evolves through execution. Some
Projects end in a paper, prototype, review, or abandoned idea; the Project note
should preserve the reasoning trail.

Projects link to Papers as evidence, to Concepts as tools or theory, to
Brainstorms as exploratory branches, and to Reviews when a synthesis supports a
deliverable.

Good practice: write the current question and next action near the top. A
Project is a working surface, not an archive.

## Brainstorm

A Brainstorm is a low-friction space for ideas that are not yet stable enough to
be Projects, Concepts, or Reviews. It is intentionally exploratory.

Create a Brainstorm when you need to think freely: research questions, possible
taxonomies, hypotheses, objections, outlines, experiment ideas, or connections
that are not yet proven. Do not over-polish it.

A Brainstorm contains fragments, sketches, lists, speculative links, and
questions. It evolves by either being refined into a Project, distilled into
Concepts, absorbed into a Review, or archived as a dead end.

Brainstorms link to Papers that triggered the idea, Concepts being explored,
Projects that might use the idea, and Reviews when the brainstorm becomes an
outline or synthesis plan.

Good practice: use Brainstorms to keep uncertainty visible. Once an idea becomes
durable, promote it into a Concept or Project rather than letting the Brainstorm
become an unstructured permanent note.

## Review

A Review is a structured synthesis across multiple sources. It is not just a
folder of Papers; it is the argument or map that emerges from comparing them.

Create a Review when you need to answer a broader question, compare a literature
cluster, write a related work section, prepare a survey, or decide what a field
currently knows. A Review is usually created after several Papers and Concepts
already exist.

A Review contains scope, inclusion criteria, key Papers, major Concepts,
contradictions, themes, gaps, and a synthesized narrative. It evolves from a
reading list to a structured map to a written argument.

Reviews link to Papers as corpus items, Concepts as themes, Projects as the
reason the synthesis matters, and Brainstorms as planning or outline material.

Good practice: define the question and scope early. A Review without scope tends
to become a vague bibliography.

## Recommended Workflow

1. Import a Paper when you identify a source worth retaining.
2. Read enough to write a short Paper note: what it claims, why it matters, and
   what you may reuse.
3. Extract or link Concepts only when an idea is reusable beyond that Paper.
4. Create a Brainstorm when the source triggers open questions, hypotheses, or
   possible structures.
5. Promote useful Brainstorm material into a Project when there is an active
   outcome.
6. Link Papers and Concepts into the Project as evidence and tools.
7. Create a Review once you have a cluster of Papers and Concepts that need
   synthesis.

This workflow is useful because it separates evidence, understanding, execution,
exploration, and synthesis. A Paper preserves source fidelity. A Concept
captures reusable knowledge. A Brainstorm protects early thinking. A Project
turns knowledge into action. A Review turns many sources into a coherent
argument.

## Architecture Check

The five object types are justified, but only if their boundaries stay strict.

Paper and Review can overlap if a Review becomes just a list of Papers. The
boundary is that a Paper is source-specific, while a Review is cross-source
synthesis.

Concept and Review can overlap if Concepts become long essays. The boundary is
that a Concept explains a reusable idea, while a Review answers a scoped
literature question.

Project and Brainstorm can overlap if every idea becomes a Project too early.
The boundary is that Brainstorm is exploratory and disposable, while Project has
a concrete outcome.

Project and Review can overlap when a Review is itself the deliverable. In that
case, the Project should track execution and decisions; the Review should hold
the synthesis.

No additional categories are needed now. If simplification becomes necessary,
the safest reduction is to treat Brainstorm as a mode or status of a note rather
than a separate long-term object. The other four types carry distinct long-term
responsibilities: sources, ideas, work, and synthesis.

The system should optimize for few objects with strong links, not many categories
with weak meaning.
