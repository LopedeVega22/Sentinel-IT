# tactiq.io free youtube transcript
# Agent Development Kit (ADK) Masterclass: Build AI Agents & Automate Workflows (Beginner to Pro)
# https://www.youtube.com/watch/P4VFL9nIaIA

00:00:00.080 Hey guys, Google just released their new
00:00:02.720 agent framework called Agent Development
00:00:04.960 Kit and it is exploding in popularity.
00:00:07.680 And in this ADK crash course, I'm going
00:00:09.840 to take you from beginner to expert so
00:00:12.240 that you can go off and build your own
00:00:14.160 AI agents, automate your workflows, and
00:00:17.279 add AI agents to your own applications.
00:00:19.760 And if you're new to the channel, my
00:00:21.279 name is Brennan Hancock and I've helped
00:00:23.119 hundreds of thousands of developers
00:00:24.960 learn how to build AI agents through my
00:00:27.119 crash courses on Langchain and Crew AI.
00:00:29.920 So, I'm super confident that I'll be
00:00:31.439 able to help you guys as well when it
00:00:32.960 comes to building AI agents with ADK.
00:00:35.360 And to help you master ADK as quickly as
00:00:38.079 possible, I've created 12 different
00:00:39.920 examples that we're going to walk
00:00:41.280 through in this crash course. And you're
00:00:42.960 going to see that we're going to start
00:00:44.079 off with the absolute basics of building
00:00:45.920 an individual agent and gradually add in
00:00:48.719 more advanced features until you're
00:00:50.480 building multi- aent workflows with tool
00:00:52.719 callings and much more. And because I
00:00:54.480 want this crash course to be as beginner
00:00:56.320 friendly as possible, we're going to
00:00:57.840 walk through every example step by step
00:01:00.079 so that we stay on the same page and so
00:01:02.160 you can see just how easy it is to
00:01:03.840 actually create AI agents with ADK. And
00:01:06.240 to make things even easier for you, I'm
00:01:08.240 giving away all the source code for all
00:01:09.840 the examples you're going to see today
00:01:11.439 completely for free. Just click that
00:01:13.119 first link in the description below so
00:01:14.560 you can download the 12 examples and
00:01:16.240 kickstart your 80k journey. But enough
00:01:18.400 talk. Let's go ahead and cover the 12
00:01:20.159 different examples that we're going to
00:01:21.280 be building together today and then dive
00:01:23.119 into creating our first agent together.
00:01:25.119 So here are the 12 different examples
00:01:27.040 that we're going to be building together
00:01:28.560 today inside of this crash course. And
00:01:30.479 as promised, we're going to start off by
00:01:32.320 building the absolute basics, and then
00:01:34.159 we're going to gradually add in more
00:01:36.000 complexity and features until you're
00:01:37.920 building some really cool multi- aent
00:01:40.079 workflows. Super excited to dive into
00:01:41.920 this. So, let's go ahead and cover these
00:01:43.600 one by one so you know exactly what
00:01:45.280 we're going to be building throughout
00:01:46.479 today. To start off, we're going to
00:01:47.920 create our first agent, which is a
00:01:49.840 single agent, so you can understand the
00:01:51.520 core principles of creating agents
00:01:53.600 inside of ADK. From there, I'm going to
00:01:55.840 show you guys how you can add tools to
00:01:58.000 provide different and more functionality
00:01:59.920 to the agents you create and how you can
00:02:02.159 access some of the pre-built tools that
00:02:04.320 Google provides you. From there, I'm
00:02:06.000 going to show you how you can bring in
00:02:07.840 other models to ADK, such as bringing in
00:02:10.720 OpenAI and anthropic models, so you're
00:02:13.599 not just stuck using Gemini. Super
00:02:15.440 excited that ADK allows for this
00:02:17.120 functionality. Next, you're going to see
00:02:18.959 how we can make sure our agents spit out
00:02:21.840 structured outputs. This is super
00:02:23.840 important to make sure our agents spit
00:02:25.599 out, you know, specific JSON structures
00:02:27.840 so that we can pass it over to other
00:02:29.840 APIs and tools. Then you're going to see
00:02:32.640 how we can update and make our agents
00:02:35.280 have session and memory so that they can
00:02:37.599 remember things between different
00:02:38.959 conversations. After that, you're going
00:02:40.640 to see how we can make our agents save
00:02:43.840 data, specifically save their session
00:02:45.920 and memory so that when we close out of
00:02:47.760 the application and open it back up,
00:02:49.440 these agents still have access to things
00:02:51.360 we talked about earlier. So, this is
00:02:52.879 where we're going to start adding in
00:02:53.760 some database functionality. After that,
00:02:55.680 things are going to start to get fun
00:02:57.120 because we're going to start working on
00:02:58.640 creating some multi- aent solutions
00:03:00.800 where we're going to have our agents
00:03:02.000 working together and we're going to
00:03:03.519 start off with the basics and then
00:03:05.200 you're going to after that start to
00:03:06.959 learn how we can add in, you know, some
00:03:08.720 session and memory to our multi- aent
00:03:10.640 solutions so they can remember things as
00:03:12.159 they're talking and working together.
00:03:13.760 Finally, what we're going to do after
00:03:15.519 that is add in the ability to add in
00:03:17.840 callbacks. And simply put, when it comes
00:03:19.840 to callbacks, agents have a certain life
00:03:22.080 cycle of things that they do before they
00:03:24.000 run, after they run, and while they're
00:03:25.840 running. And call backs allow you to
00:03:27.599 control every part of the agent life
00:03:29.599 cycle. Really excited to showcase this
00:03:31.360 functionality. And then finally, what
00:03:33.120 we're going to work on is talking about
00:03:35.599 different workflows that you can access
00:03:38.080 inside of ADK. So, we're going to start
00:03:40.080 off with working on sequential agents
00:03:42.080 where we make sure agents always work in
00:03:44.720 a specific order. agent one, two, then
00:03:46.959 three. They always work left to right.
00:03:48.560 Next, you're going to see how we can
00:03:50.080 make our agents work in parallel to our
00:03:52.239 agents. We're going to have three or
00:03:53.599 four agents working on task in parallel.
00:03:55.680 And then when they're done, they're all
00:03:56.879 going to come together and combine their
00:03:58.799 answer. And then finally, you're going
00:04:00.319 to see how we can add in loops to our
00:04:02.560 agents where our agents are going to
00:04:04.239 continually work over and over and over
00:04:06.000 until they achieve a desired output.
00:04:08.400 Super excited. So, you guys are going to
00:04:09.920 go from a complete beginner to an
00:04:12.000 absolute pro after going through all
00:04:13.439 these different examples. So, let's go
00:04:15.040 ahead and dive into our first example of
00:04:16.720 building your first agent with ADK. So,
00:04:18.959 welcome to the first example inside the
00:04:20.880 ADK crash course where we're going to
00:04:23.040 focus on building and running your first
00:04:25.759 single agent. And inside of this first
00:04:28.160 example, we're going to walk through
00:04:29.440 five steps together. First, I'm going to
00:04:31.759 cover the core attributes of building
00:04:33.840 your agent so you can understand how all
00:04:35.680 the different properties work together
00:04:37.440 in order to run your agent. Next, we're
00:04:39.600 going to cover the folder structure of
00:04:41.919 creating your agent. And this is super
00:04:43.520 important because ADK requires a
00:04:46.000 particular format in order for you to
00:04:48.000 run your agents. Third, I'm going to
00:04:49.919 walk you through the process of
00:04:51.680 installing your proper dependencies in
00:04:54.160 order to run all the agents that you're
00:04:56.240 going to see in this crash course today.
00:04:57.840 The fourth thing I'm going to show you
00:04:58.960 how to do is access and download an API
00:05:02.080 key just like this so you can run your
00:05:04.560 agents. And then the fifth thing that
00:05:06.080 we're going to cover today is running
00:05:08.000 your agents. So, this is where we're
00:05:09.280 going to kick things off so you can
00:05:10.479 begin to chat with your agents and see
00:05:12.400 just how effective they are at following
00:05:13.919 instructions and just how easy it is to
00:05:15.600 run inside ADK. So, without further ado,
00:05:17.440 let's go ahead and cover our first agent
00:05:19.280 together. So, when it comes to creating
00:05:20.720 your first agent inside of ADK, let's
00:05:23.120 walk through each of the core
00:05:24.320 components. So, first things first,
00:05:26.080 inside of ADK, you need to make sure you
00:05:28.800 have at least one root agent. This is
00:05:31.440 the entry point to all the requests that
00:05:33.840 you're going to start sending over to
00:05:35.759 all of your agents. So you need to make
00:05:37.440 sure that you have a root agent. From
00:05:39.039 there, when it comes to your agents,
00:05:40.880 there's a few core properties that
00:05:42.080 you're going to use over and over and
00:05:43.520 over. The first one is going to be the
00:05:45.680 name of the agent. As we run the agent
00:05:48.080 later on, you're going to see this name
00:05:50.080 pops up so we can say who's actually
00:05:52.080 taking responsibility and generating the
00:05:54.320 results for each of the requests we send
00:05:56.000 in. It's super important that the name
00:05:58.560 of this agent, greeting agent, matches
00:06:01.840 the agent name over here. So you can see
00:06:04.080 greeting agent inside of our folder
00:06:05.759 structure. It must match this name right
00:06:08.160 here. If they don't match, ADK is going
00:06:10.160 to throw a fit and say, "Hey, I don't
00:06:12.000 recognize this. I don't see it
00:06:13.120 anywhere." So, let's make sure they
00:06:14.479 match. The next thing that you're going
00:06:16.319 to need to put in all of your agents is
00:06:19.199 a model. Now, as I mentioned earlier,
00:06:22.160 you can use any model from any
00:06:23.759 framework. We'll talk more about this
00:06:25.120 later on. So, you can bring in your
00:06:26.400 Claude or OpenAI, but the easiest models
00:06:28.479 to use are going to be your Gemini
00:06:30.319 models. Now, for this tutorial, we're
00:06:32.000 going to use Gemini 2.0 no flash for
00:06:33.680 everything. But if you want to see all
00:06:35.840 the other models that ADK or
00:06:37.919 specifically Google has to offer, you
00:06:40.000 can click this link right here and it'll
00:06:41.680 take you over to their model dashboard
00:06:43.600 right here. So you can see there are a
00:06:45.759 few core models that they offer.
00:06:47.520 Everything from Gemini 2.5 Pro, which is
00:06:50.240 their smartest, most powerful model.
00:06:52.319 They also have the 2.0 Flash, which is a
00:06:54.560 toned down version of it. It's not as
00:06:56.080 smart, but it's still really fast. Or
00:06:57.759 they have their 2.0 no flash model which
00:07:00.160 has access to all of the multimodal
00:07:02.560 features such as images, audio,
00:07:04.720 everything else. So, this is the one
00:07:06.240 we're going to be using throughout the
00:07:07.919 rest of this crash course. But what you
00:07:10.160 could also see if you want to check out
00:07:12.479 on pricing, you can come down one tab
00:07:14.880 right here and review the pricing for
00:07:16.639 each of the models. So, you can see in
00:07:18.720 our case, we are using Gemini 2.0 no
00:07:20.720 flash. And you can see when it comes to
00:07:22.479 pricing for this model, it cost about 10
00:07:25.039 cent per million tokens, which is wild
00:07:27.919 how cheap it is, for how smart this
00:07:29.280 model is. And then when it comes to
00:07:30.720 output prices, you can see it cost 40.
00:07:33.280 So all around, this is a super super
00:07:35.199 affordable model. And it's insanely
00:07:37.199 capable as well. And it has a 1 million
00:07:39.599 token context window, which is insane
00:07:41.759 for how much information we can pass
00:07:43.199 into this model. Okay, enough about the
00:07:45.199 model though. Let's go go go back and
00:07:47.039 cover the two other properties that
00:07:49.120 you're going to see in every agent going
00:07:50.639 forward. So, the next property is going
00:07:52.720 to be the description. Now, the
00:07:54.240 description will come more in play as we
00:07:56.720 create our multi- aent solutions. But
00:07:59.039 basically, when we're working with
00:08:00.400 multi- aent solutions, the root agent is
00:08:03.440 always looking to say, hm, I'm trying to
00:08:05.759 work on this task. What other agents do
00:08:08.160 I have access to that would do a better
00:08:10.479 job at working on this task? So this
00:08:13.039 description is a highle basically job
00:08:15.520 overview of like hey I am this agent and
00:08:18.560 here's what I specialize in doing and if
00:08:21.199 you know if it was a copywriting agent
00:08:23.360 so someone who specialized in writing
00:08:24.879 the agent would go oh I'm working on a
00:08:26.720 writing task right now cool I need to
00:08:28.720 delegate to this other agent long story
00:08:30.479 short it is to help agents figure out
00:08:32.640 who they should delegate work to in a
00:08:34.479 single agent though there's no
00:08:35.679 delegation so we wouldn't need it okay
00:08:37.599 now the final one and the most important
00:08:39.200 one is going to be the instructions and
00:08:41.519 the instructions are just like it sounds
00:08:43.200 like. These are the instructions for
00:08:44.880 telling the agent what it should do and
00:08:46.560 how it should do it. So, you're going to
00:08:48.399 see as we go out throughout the rest of
00:08:49.920 this tutorial how we add in some really
00:08:51.760 complicated instructions and Gemini 2.0
00:08:54.480 Flash is just going to handle it like an
00:08:56.000 absolute charm. So, now that you've seen
00:08:57.760 the core attributes of an agent, let's
00:09:00.320 go ahead and start talking about the
00:09:02.399 folder structure and why things are set
00:09:04.399 up the way they are. So, here's
00:09:05.760 everything you need to know about the
00:09:07.279 folder structure of working with agents
00:09:09.040 inside of ADK. So, first things first,
00:09:11.440 inside of every project we work on,
00:09:13.760 we're going to put our agents in folders
00:09:17.040 just like this. And we are going to have
00:09:19.360 a few core components in each one. We're
00:09:22.160 going to have an init.py file and we're
00:09:24.480 going to have av and we're going to have
00:09:26.959 an agent. So, let's walk through what
00:09:28.560 each one of these does at a high level.
00:09:30.240 When it comes to our init.py file, this
00:09:33.120 is basically telling Python, hey, I have
00:09:35.920 some important information in here that
00:09:37.440 you need to look out. In the case of our
00:09:39.279 ADK agents, we're saying, "Hey, in this
00:09:43.040 folder, that's what the dot means. I
00:09:44.880 have an agent that you need to work on
00:09:47.040 importing." So, this agent is basically
00:09:49.600 pointing at this agent.py right here.
00:09:51.519 Okay. So, that's the important thing. An
00:09:53.040 ADK, it needs to know what agents it has
00:09:55.360 access to. All right. The next one that
00:09:57.600 you need to look at is thev file. Thev
00:10:00.480 file is where you're going to store all
00:10:02.480 your environment variables for your
00:10:04.560 agents and all the other projects you
00:10:06.880 work on. Now, what's important to note
00:10:08.320 is you only need to have one EMV file
00:10:11.600 and you need to keep it inside of your
00:10:13.519 root agent. And in this case, we only
00:10:15.519 have one agent. So, we only have to put
00:10:17.519 it one place. Basically, it just goes in
00:10:19.279 the root agent. However, later on,
00:10:21.360 you'll see whenever we start to work on
00:10:22.959 multi-agent solutions, we're going to
00:10:24.640 have a bunch of agents and you don't
00:10:26.160 need to put a&b in all of them. You just
00:10:28.000 need to keep it in the root one. So,
00:10:29.279 hopefully that makes sense. And then
00:10:30.560 finally, the other thing is you need to
00:10:33.040 have your agent.py file. And a quick
00:10:35.600 reminder, you need to make sure that the
00:10:38.000 name of this agent matches the folder.
00:10:40.800 It has to be 1:1 or else it's going to
00:10:43.120 throw some errors at you. And to make
00:10:44.959 your life easier, speaking of a while
00:10:46.800 back when I was showing thev file is
00:10:48.959 I've created example for you. So when
00:10:51.279 you're working on this on your own,
00:10:52.640 you're just going to rename this toenv
00:10:55.839 instead of example and then you're going
00:10:58.240 to paste your API key here. Yeah. So
00:11:00.320 that is the folder structure at a
00:11:02.240 nutshell. Now, what I want to do is walk
00:11:04.480 you through how you can install all the
00:11:06.720 dependencies to actually run this agent.
00:11:09.360 So, in order to do that, let me show you
00:11:11.040 all the different commands you need to
00:11:12.399 run. And I've got some source code and
00:11:14.560 instructions to help make this even
00:11:15.839 easier for you guys. So, when it comes
00:11:17.360 to installing all the dependencies in
00:11:19.360 order to run this crash course, I've
00:11:21.200 tried to make it as easy as possible for
00:11:22.640 you guys. So, first things first, there
00:11:24.560 is a
00:11:25.480 requirements.txt file. And basically all
00:11:27.839 this does is it calls out the different
00:11:30.240 packages that we want to install. The
00:11:32.240 most important one is obviously Google
00:11:33.680 ADK because this is what's going to give
00:11:36.000 us access to the agent development
00:11:37.519 framework. From there, I have a few
00:11:39.760 other different libraries and
00:11:41.839 dependencies that you guys are going to
00:11:43.440 need. And you don't need them all now,
00:11:45.040 but I've tried to set it up so that you
00:11:46.959 guys only have to run the install
00:11:48.320 command once and then you're good for
00:11:50.000 the rest of the project. Okay. So, what
00:11:52.399 we need to do is follow some
00:11:54.160 instructions that I have set up for you
00:11:55.920 guys to create an environment. Now, if
00:11:58.000 you're very new to programming,
00:11:59.920 basically when it comes to working with
00:12:02.160 Python, every time you work on a
00:12:03.760 project, you want to create an
00:12:05.040 environment. That environment is going
00:12:06.880 to install and contain all of the
00:12:09.839 different libraries and dependencies you
00:12:11.600 need. The reason why you want to do this
00:12:13.040 is because each project has its own
00:12:14.720 requirements, and you don't want to
00:12:16.160 accidentally install all the
00:12:17.519 requirements from project A, B, and C
00:12:19.600 into one environment because it's going
00:12:20.800 to just cause a ton of errors. So, we're
00:12:22.880 going to create a single environment for
00:12:24.399 this. install all the required
00:12:26.160 dependencies and then we're good to run
00:12:28.000 everything. So, here are the
00:12:29.200 step-by-step instructions to create your
00:12:31.040 virtual environment. And you can find
00:12:32.720 these by looking inside of the root
00:12:34.560 folder of the crash course. I have a
00:12:36.079 read me right here for you guys. So,
00:12:37.680 here are the commands we're going to run
00:12:39.120 together one at a time. So, the first
00:12:40.800 one is we are going to create a virtual
00:12:43.120 environment inside the root directory of
00:12:44.880 your project. though you can open up
00:12:47.040 your terminal and type in the command
00:12:48.959 right here. Python make a virtual
00:12:51.120 environment and then put the virtual
00:12:53.440 environment in thevnb folder. So I'm
00:12:56.079 going to run this and I'm going to show
00:12:57.040 you what it does. So it just ran and now
00:12:59.839 you can see in the top left corner of
00:13:02.160 your file explorer you can see we have a
00:13:03.920 new folder. It's a blank virtual
00:13:05.600 environment that has a few key
00:13:07.600 components of what's necessary to run a
00:13:10.000 Python environment. Now from there what
00:13:11.839 we can do is we need to activate this
00:13:14.560 new environment. So I'm on a Mac so I'm
00:13:17.360 going to run this command but if you're
00:13:19.040 on Windows you can run these commands
00:13:21.279 right here. So let's go ahead and paste
00:13:22.800 it in. And what this will do is it will
00:13:24.720 now say hey you are now working with
00:13:27.279 this virtual environment right here. And
00:13:29.680 this is where what's going to allow you
00:13:31.360 to install all of your dependencies. I
00:13:33.680 actually just really quickly need to get
00:13:35.360 out of another environment. Deactivate.
00:13:38.079 You don't need to run that command. I
00:13:39.440 just needed it. I was uh in a weird
00:13:40.880 state. Okay, cool. So, now that we have
00:13:42.959 everything set up, what you can do is
00:13:45.279 install all of the dependencies. And
00:13:47.519 what this will do is it will install all
00:13:49.120 the dependencies and put them inside
00:13:50.720 your virtual environment. So, you can
00:13:52.320 see right now we barely have any
00:13:54.000 packages in here. But when I run this
00:13:56.000 command, what it's going to do is it's
00:13:57.839 going to install everything that we
00:13:59.600 called out right here, all of these. And
00:14:02.000 you will see in just a second, this
00:14:03.760 virtual environment is going to include
00:14:05.440 a ton more packages. everything from
00:14:07.279 Google ADK, some stuff to look up
00:14:09.440 finance stocks that we're going to do
00:14:10.480 later on, and yeah, tada. It now has a
00:14:12.800 ton of additional packages. Okay, great.
00:14:15.600 So, that is pretty much set up. And now
00:14:17.760 what we can do is we are officially done
00:14:20.079 with installing all of our different
00:14:21.760 Python requirement packages in order to
00:14:24.399 run this project. So, tada, everything
00:14:26.399 is done. So, now we can move on to step
00:14:28.320 four, which is where I'm going to show
00:14:30.079 you how you can access an API key to run
00:14:33.120 everything that we're going to be
00:14:34.399 working on today. So, let me quickly
00:14:36.000 walk you through how you can create your
00:14:37.680 own API key. So, what we can do is
00:14:40.000 follow the rest of the readme
00:14:41.600 instructions and we're going to walk
00:14:43.839 through these steps right here. So,
00:14:45.519 first things first is we need to go over
00:14:48.079 to Google Cloud and create an account.
00:14:50.800 So, what you'll do is hop over to Google
00:14:53.279 Cloud just like this and you'll need to
00:14:55.519 sign up and create account if you
00:14:57.040 haven't. Once you do create account,
00:14:58.800 you'll click console. And this will take
00:15:01.120 you to this page right here where you're
00:15:03.519 basically in your root dashboard. And
00:15:05.199 what we want to do is click in the top
00:15:07.040 lefthand corner because we're trying to
00:15:08.560 create a project. We want one project to
00:15:10.720 run all these examples. So we'll click
00:15:13.120 create new project. And I will call this
00:15:16.720 we'll call it YouTube ADK crash course
00:15:21.440 just like this. And what I can do from
00:15:23.680 there crash course. And then what you
00:15:25.760 can do from there is you might not have
00:15:27.360 a billing account set up. You will need
00:15:29.680 to create one and this is what will be
00:15:32.079 charged to as you create your own
00:15:34.800 request inside of this examples cuz if
00:15:37.360 you remember Gemini Flash 2.0 costs like
00:15:39.839 10 cent per million tokens. So it's
00:15:42.240 going to like you might get charged a
00:15:43.680 penny by running all this project. But
00:15:45.519 you need to create a billing account.
00:15:47.279 Now if this is your first time creating
00:15:48.639 a Google Cloud Platform account, you'll
00:15:50.480 probably get a bunch of free credits. So
00:15:51.839 you might not have to go through this
00:15:52.959 process. But I still just want to show
00:15:54.240 it to you. So once you're done, you're
00:15:55.759 going to click create. And then tada,
00:15:58.079 it's going to create all of your project
00:16:01.040 and all the necessary underlying assets
00:16:03.440 for it. And you can see once it's fully
00:16:05.440 done, you can click select project. And
00:16:07.519 what this will do is in the top lefthand
00:16:09.360 corner, you can now see that you are
00:16:11.279 working on the project you just created.
00:16:13.120 Great. So let's head back over to our
00:16:15.759 instructions because we just checked off
00:16:17.199 one and two. And now we want to create
00:16:20.000 an API key. So we're going to go to this
00:16:21.759 link. So, I'm going to go ahead and
00:16:22.959 paste it in and it will take us to a
00:16:24.720 page just like this. Now, you might have
00:16:26.560 to sign up for AI Studio. It's a little
00:16:28.240 weird. I can't remember if you have to
00:16:29.120 sign up for Google Cloud and both. So,
00:16:30.560 you might have to do an extra sign up
00:16:31.759 step. But the important thing is you can
00:16:33.839 now click the create API key button. So,
00:16:36.560 we're going to click this create API
00:16:38.240 key. And we are going to type in the
00:16:40.639 name of our project, which is YouTube
00:16:42.560 ADK crash course. Once this is done,
00:16:44.720 it's going to say create API key. And it
00:16:47.680 should take just a few seconds to create
00:16:49.680 that API key, but you need to copy it.
00:16:51.839 So great, we're going to copy it. And
00:16:53.839 please don't share this with anyone
00:16:55.199 else. I'm going to delete mine right
00:16:56.480 after the video, but click copy. And you
00:16:58.880 are going to go over to your VNV file.
00:17:02.720 So basics agent, greeting agent, and
00:17:05.520 paste it right in here. So this is how
00:17:07.839 you're going to set up your agent and
00:17:09.760 and actually have it access your API
00:17:12.240 keys that you just set up. Fantastic.
00:17:14.480 So, we're now good. And you can refresh
00:17:16.880 just to make sure it all worked.
00:17:18.400 Fantastic. So, now if you look at mine,
00:17:20.480 it's going to say YouTube ADK crash
00:17:22.640 course. And mine was already hooked up
00:17:24.480 to a billing plan cuz you just walked
00:17:26.000 through that with me as well. So, you
00:17:27.359 are good. Things are great. You can now
00:17:29.120 start to use this API key to make
00:17:31.520 request. So, now we're at the final
00:17:33.840 step, which is going off and and running
00:17:36.880 the actual agent itself. So, you can see
00:17:38.720 it in action. So, let me show you how
00:17:40.240 you can start to do that. And the first
00:17:42.160 things first is we are going to clear
00:17:44.080 out our terminal so that we can run our
00:17:46.320 special commands to get everything
00:17:47.679 working. So in order to run this agent,
00:17:49.679 the first thing we need to do is change
00:17:51.840 directory to make sure we are inside the
00:17:54.160 basic agent folder. So you're going to
00:17:56.320 cd and go into the basic agent folder.
00:17:58.960 Great. So if we look in here, yep, we
00:18:00.400 can see we have our greeting agent.
00:18:01.679 Things are looking good. Now the special
00:18:03.520 command that we are trying to run is
00:18:05.760 called ADK. This is the CLI, command
00:18:09.039 line interface tool for using agent
00:18:11.679 development kit. So if you just type in
00:18:13.200 ADK by itself, it's going to show you
00:18:15.760 all the different options that you can
00:18:17.440 run. So you can run these all of these
00:18:20.000 right here. Now let's walk through them
00:18:21.520 and then I'm going to show you the one
00:18:22.320 we're going to use. So first things
00:18:23.840 first, you could run the API server. And
00:18:26.720 basically what this will do is it will
00:18:28.880 create a endpoint so you can start to
00:18:31.280 make API requests to your agent. So
00:18:33.840 you'll be able to do like a quick
00:18:35.600 request to like localhost slash API
00:18:39.520 slash and then make a request to your
00:18:41.039 agents. So that's what you could do
00:18:42.480 there. The next one is you could run
00:18:44.799 adkreate and this would create an agent
00:18:47.440 folder for you. We have already have
00:18:49.679 everything set up so you don't need to
00:18:50.720 run create. Then it has a few extra
00:18:52.559 commands you can run such as deploy
00:18:54.480 which will deploy your agents to the
00:18:56.080 cloud. I have a full tutorial on that.
00:18:57.760 Definitely recommend checking that on my
00:18:59.039 channel. Then you have eval which is
00:19:00.640 basically like running test against your
00:19:02.480 agent. a little outside the scope of
00:19:04.000 this tutorial, but I'll have one coming
00:19:05.679 up later. The next one is run, which
00:19:08.880 will run the agents inside your
00:19:11.520 terminal. So, you would be typing inside
00:19:13.200 of your terminal right here to chat with
00:19:14.880 your agents. And the best one that we're
00:19:16.720 going to be using is ADK web. And this
00:19:18.880 will spin up a really nice looking
00:19:20.400 website for us to chat with our agents
00:19:22.240 and give us access to seeing a lot of
00:19:24.240 the underlying events and state and
00:19:26.960 everything else that's going on inside
00:19:28.480 of our agents. So, let me show you how
00:19:30.559 you can run this. So, we're going to
00:19:32.000 type in ADK web. And what this will do
00:19:35.600 is spin everything up. And you can now
00:19:37.919 see, all right, great. Your web server
00:19:40.080 has started. You can go to this link to
00:19:42.880 access the agents. So, we're going to
00:19:44.960 hop over to our browser. Go over and you
00:19:48.000 can now see that we have our web server
00:19:50.559 up and running and we have access to our
00:19:52.480 agents. So, let me give you a quick
00:19:53.919 overview of what's happening and then
00:19:55.600 we're going to start chatting with it.
00:19:56.960 So up in the top lefthand corner, you
00:19:58.880 have the ability to pick which agent you
00:20:00.880 want to talk to. In our case, we only
00:20:02.799 have a single agent. So it auto picks,
00:20:04.960 oh, you're trying to chat with the
00:20:06.160 greeting agent. Now, we're going to talk
00:20:07.840 about a lot of these later on, but just
00:20:10.880 know events are as we chat with our
00:20:12.880 agent, you're going to be able to see
00:20:14.000 like, oh, event one happened where we
00:20:15.760 were trying to figure out who to work
00:20:16.799 with and we made a response and you can
00:20:18.960 see in real time all the events that
00:20:20.799 happen. State, this is where we are
00:20:23.120 going to store information with our
00:20:25.280 agents. We're going to hop on to this in
00:20:27.679 module five. Artifacts outside the scope
00:20:30.000 of this tutorial. A session. A session
00:20:31.840 is nothing more than a series of
00:20:33.360 messages between us and the agent. So,
00:20:36.400 you know, we can create multiple
00:20:37.520 sessions to where we can have multiple
00:20:38.880 different chats with the agent. And then
00:20:41.039 the final one is vows, but we're not
00:20:42.640 working on that in in here. Okay. So,
00:20:44.480 let's go ahead and start testing out
00:20:46.880 this agent. And as a quick reminder,
00:20:49.600 this agent, we have told it to follow
00:20:51.919 these instructions. you are a helpful
00:20:53.600 assistant that greets the user. Ask the
00:20:55.919 user's name and greet them by their
00:20:57.679 name. So what we can do is say, hey, how
00:21:00.400 are you? And then we can see the agent
00:21:02.559 follows these instructions. To make
00:21:04.320 things a little bit more personal,
00:21:05.520 what's your name? My name is Brandon.
00:21:08.720 And from there, the agent will go, hey,
00:21:10.480 Brandon. It's greeting me by name. And
00:21:12.080 you can see it actually working and
00:21:14.000 following these instructions. Now,
00:21:16.080 speaking of what I was talking about
00:21:17.440 earlier is events. So every time I made
00:21:20.480 a request, you could see these events in
00:21:22.880 real time. And this is one of my
00:21:24.400 favorite parts of ADK is their the ADK
00:21:27.520 web feature because it allows you to
00:21:29.440 explore what's happening with the agents
00:21:31.600 in a super interactive fashion. So you
00:21:33.840 can now see all right for our first
00:21:35.760 event, we only had one agent up and
00:21:38.159 running. And you can see the message
00:21:40.240 that was passed into it. Sorry, you can
00:21:42.000 see the response from the agent. And if
00:21:44.640 you were to dig deeper into the event,
00:21:46.640 you can see the request and the
00:21:49.120 response. In the request, you can see
00:21:51.919 the a few things. You can see the
00:21:53.840 initial instructions. So this is were
00:21:56.080 the initial instructions that we passed
00:21:58.080 in. And it also adds the description of
00:22:02.000 the agent as well. So basically, it's
00:22:04.320 taking this information right here, the
00:22:06.799 description and instruction, and putting
00:22:08.960 it all into the system instructions.
00:22:11.440 That's what it's doing under the hood.
00:22:12.799 And then you can see the initial message
00:22:14.559 we gave it. So, hey, how are you? That's
00:22:16.320 what's popping up right here. And then
00:22:17.919 finally, you can see in the response, it
00:22:20.080 generates the response. So, yeah, that's
00:22:22.240 everything that you need to know when it
00:22:23.840 comes to creating and running your first
00:22:26.320 agent. And just as a quick reminder, you
00:22:28.720 guys are now a pro at understanding how
00:22:32.080 to create an agent, the core properties.
00:22:34.480 You're also a pro at understanding the
00:22:36.880 folder structure of why we need to set
00:22:38.960 up things the way we need to do. you
00:22:40.960 know how to get your API keys and you
00:22:43.200 know how to run your agents. So, what
00:22:45.520 we're going to do next is hop over to
00:22:46.880 the second example where you're going to
00:22:48.559 start to see how we can add in some tool
00:22:50.640 functionality and access some of the
00:22:52.400 cool pre-built tools that Google gives
00:22:54.159 us. Super excited so you could see this
00:22:56.000 in action and start leveling up your
00:22:57.360 agents. Let's go ahead and hop over to
00:22:58.799 example number two. Hey guys, and
00:23:00.400 welcome to example number two where
00:23:02.320 we're going to look at adding tools to
00:23:04.799 your agents so that you can add in
00:23:06.640 additional functionality and supercharge
00:23:08.640 your agents. And in this example, we're
00:23:10.720 going to walk through four different
00:23:12.400 items. First, we're going to cover the
00:23:14.480 different types of tools you can use
00:23:16.080 with your agent because ADK is super
00:23:18.240 flexible. Next, I'm going to show you
00:23:20.000 how you can actually add these tools to
00:23:22.240 your agents. Third, we're going to cover
00:23:24.320 some of the best practices that you need
00:23:26.159 to know about when building your custom
00:23:27.840 tools. And then, we're going to also
00:23:29.679 cover a few limitations that you need to
00:23:31.679 know about when building tools. And then
00:23:33.360 fourth, we're going to go off and run
00:23:35.520 one of these agents with some tools so
00:23:37.120 you can see everything in action. So
00:23:38.640 let's go ahead and quickly cover the
00:23:40.640 three different types of tools you can
00:23:42.559 use inside ADK. So the three different
00:23:44.559 types of tools you can use inside ADK
00:23:46.720 are function calling tools, you can use
00:23:48.960 some built-in tools provided by Google,
00:23:50.880 and then you can use thirdparty tools.
00:23:52.559 So let's walk through each one of these
00:23:53.760 one at a time. So when it comes to
00:23:55.280 function tools, this is what you're
00:23:56.480 going to be using 99% of the time. This
00:23:58.559 is where you create a Python function
00:24:00.960 that you then pass over to your agent.
00:24:02.799 So you can say, "Hey, like go find the
00:24:05.200 weather, go look up stocks, whatever you
00:24:07.280 want to do." This is what you're going
00:24:08.880 to be doing most of the time where you
00:24:10.080 create your own custom Python functions.
00:24:12.159 Now, you could also use agents as tools.
00:24:15.200 This one is a little bit more
00:24:16.320 complicated and you'll see it in action
00:24:18.240 later on when we work on multi-agent
00:24:20.080 solutions, but there is a scenario when
00:24:22.080 you'd want to wrap an agent as a tool.
00:24:24.240 We'll talk about that later. Then there
00:24:25.919 are longunning function tools. This is a
00:24:28.159 little out of scope of this crash course
00:24:29.919 cuz it gets a little bit more
00:24:30.880 complicated, but just know it is
00:24:32.240 possible. The next thing that you can do
00:24:34.240 is use some of the pre-built tools
00:24:36.240 Google provided such as Google search
00:24:38.640 code execution and then rag. In this
00:24:41.279 example, we're actually going to look at
00:24:43.200 how you can use Google search inside of
00:24:45.360 your tools, which is super powerful that
00:24:46.960 you get it out of the box. A few
00:24:49.039 important things to note before we dive
00:24:50.640 in. Built-in tools only work with Gemini
00:24:53.520 models. So, if you're using OpenAI or
00:24:55.919 Claude, any of those, these built-in
00:24:57.840 tools will not work. I had to find that
00:24:59.360 out the hard way. And the third option
00:25:01.360 is to use thirdparty tools. So if you've
00:25:03.840 used the lang chain or crew AI, you can
00:25:06.320 easily add in some of the tools in the
00:25:08.960 libraries for these different frameworks
00:25:11.120 and bring them over to ADK. A little
00:25:13.600 outside the scope of this, but just know
00:25:15.120 it is possible. And basically ADK is
00:25:17.360 trying to make it as open as possible to
00:25:20.080 all the models and tools that you could
00:25:21.440 ever want so you can easily build agents
00:25:23.440 and get them up and running. So, now
00:25:24.880 that you've seen the different types of
00:25:25.919 tools we can use, let's hop over to the
00:25:27.679 code so you can see how you can start to
00:25:29.440 add tools to your agents. So, let's go
00:25:31.760 ahead and hop back over to the code.
00:25:33.039 Okay, so here is a super simple example
00:25:35.440 of an agent using the Google search
00:25:37.760 tool. Now, I do want to call out a few
00:25:39.600 things just because we are still working
00:25:41.679 our way up on becoming an ADK pro. So,
00:25:44.159 per usual, we are inside of a agent
00:25:47.679 folder. This one's called tool agent.
00:25:49.760 So, that's why we call this tool agent.
00:25:51.440 They must match. Like we said earlier,
00:25:53.120 we've picked the model and we've given a
00:25:55.200 description just like we normally do.
00:25:56.559 And the main change that you're going to
00:25:58.080 notice now is we've created a new
00:26:00.720 property and added it called tools. This
00:26:03.440 is going to be a list of all the
00:26:06.080 different tools you want to use with
00:26:08.320 your agent. And in this case, we are
00:26:10.960 going to use the pre-built tool from
00:26:12.799 Google search. And as mentioned just a
00:26:14.720 second ago, there are some additional
00:26:16.720 built-in tools that you could use. So
00:26:19.039 there is the Vertex AI search. So if
00:26:21.919 you're going to be doing any rag
00:26:23.120 queries, you can do this as well. And
00:26:24.960 there's also the built-in code execution
00:26:27.440 tool. Now it is important to note that
00:26:29.919 when using agents just like this, you
00:26:32.240 can only pass in one built-in tool at a
00:26:35.279 time. So you could not do the Vertex AI
00:26:38.320 search capabilities plus the code
00:26:40.159 execution capabilities. You can only use
00:26:42.159 one built-in tool at a time. So that's
00:26:44.400 super important to note as you're
00:26:45.760 creating these agents and working with
00:26:47.520 built-in tools. So, now that you've seen
00:26:49.039 a built-in tool, I want to go ahead and
00:26:51.760 show you how you can also add in some
00:26:54.400 additional tools as well. So, one of the
00:26:56.880 other types, the first type that we
00:26:58.559 talked about was adding in your own
00:27:00.320 Python code as functions. So, let me
00:27:02.799 show you what that looks like. So, what
00:27:04.720 you could do is create a function called
00:27:07.520 get current time. And let me walk
00:27:08.960 through a few of the important things so
00:27:10.480 we can get this up and running. So, we
00:27:12.799 can do let me get all the imports
00:27:14.320 working so you guys can see it in
00:27:15.840 action. Fantastic. So here is another
00:27:18.880 example of a tool and this is why I like
00:27:21.600 this one so much. So you can see in
00:27:24.240 order to create your own custom Python
00:27:26.960 tool, all you need to do is make a
00:27:28.960 function. You need to specify a few
00:27:31.840 other things. You need to specify the
00:27:34.080 return type. You need to specify a dock
00:27:37.039 string. A dock string, just in case
00:27:38.640 you're not familiar with it, this is how
00:27:40.720 the agent determines what the function
00:27:42.880 does and if it should call it. So if we
00:27:45.279 give it a command saying, hey, please
00:27:47.919 fetch the current time. Well, the agent
00:27:50.559 will look through all the available
00:27:52.000 tools that we have down here and it will
00:27:55.120 see like, oh, I can see right now that I
00:27:57.760 have access to the get current time
00:27:59.360 tool. So I know because I have access to
00:28:01.919 this tool and I know what this tool
00:28:03.600 does. Yes, this is the tool I need to
00:28:05.600 use to solve this problem. Now, there
00:28:07.360 are a few other things when it comes to
00:28:09.039 best practices that you need to know
00:28:10.880 when creating tools. First things first,
00:28:14.320 whenever you are returning the results
00:28:16.880 of a tool, the agent framework wants you
00:28:20.080 to be as specific and as instructional
00:28:24.240 as possible. And sorry if that's not a
00:28:26.080 word, but what I mean by that is it's
00:28:28.000 super common for a lot of the time when
00:28:29.679 people want to return stuff is they'll
00:28:31.760 just go, "Oh, okay. I'm just going to
00:28:33.600 return the results." Well, you don't
00:28:36.159 want to do this because when the result
00:28:39.279 gets passed back to the agent, it's not
00:28:41.120 going to know like, well, what is this?
00:28:42.640 Like, did you give me the current time?
00:28:44.080 What what is this? So, when you are
00:28:46.399 returning results back to your agent so
00:28:48.960 that it can read the results and use the
00:28:51.120 results in the answer it generates, you
00:28:53.120 want to make sure the dictionary you
00:28:55.279 create is as robust as possible. And if
00:28:58.080 for whatever reason you do return
00:29:00.399 something, just say like this for
00:29:02.080 example, let's just say you return
00:29:03.600 hello. What ADK is going to do under the
00:29:06.559 hood is it is going to wrap the return
00:29:09.520 statement into a to something like this
00:29:12.399 where it's going to do result and then
00:29:14.159 it's going to do hello. So ADK is going
00:29:16.640 to do its best to wrap the results and
00:29:18.640 it's always going to convert it to a
00:29:20.799 dictionary just like this. So we want to
00:29:22.880 be as helpful as possible and instead of
00:29:25.200 ADK having to do the work and just
00:29:26.960 saying generic result, we want to say
00:29:29.600 no, this is actually the current time.
00:29:31.120 This is the key and this is going to be
00:29:32.880 the value. Now a few other things that
00:29:34.640 didn't show in this example is sometimes
00:29:37.760 you want to pass in variables. So
00:29:40.320 whenever you want to pass in variables
00:29:42.720 what you can do is just say I want to do
00:29:45.840 format and then what you can do is pass
00:29:49.120 in the type of it. So in this case we
00:29:51.919 want to do a string. Now what you can
00:29:54.240 notice is my current time function now
00:29:57.600 includes a default value. This is what a
00:29:59.600 default value looks like. It's when you
00:30:01.440 have a property or a parameter and then
00:30:04.320 you pass in some values after it.
00:30:06.640 Default properties do not work inside
00:30:08.880 ADK at the time of this recording. So
00:30:11.760 never add in default values. They won't
00:30:13.600 work and things will break. So instead,
00:30:15.919 what you want to do is just pass in your
00:30:18.559 properties with the types just like this
00:30:20.640 and use them however you want. Okay,
00:30:22.399 cool. So you've now seen how to create a
00:30:24.559 tool and you've seen how easy it is to
00:30:27.039 add tools to your agents. The only other
00:30:30.399 thing I want to mention when it comes to
00:30:32.720 some limitations is ADK when it comes to
00:30:35.919 built-in tools is super particular.
00:30:38.480 Meaning, if you wanted this tool to
00:30:40.720 search to use Google search, great. That
00:30:42.799 could work. If you wanted to work with
00:30:45.520 current time and add in a few extra
00:30:47.760 custom functions, great, you can do
00:30:49.600 that. But what you can't do is add in
00:30:52.640 built-in tools with custom tools. ADK
00:30:55.840 breaks whenever you do that. So, I just
00:30:57.600 wanted to call out this before we
00:30:59.520 actually used it so that you could
00:31:01.360 understand some of the limitations cuz
00:31:02.720 when I was playing around with ADK for
00:31:04.159 the first time and this was breaking on
00:31:05.919 me, I could not understand why it was
00:31:07.679 breaking. So, hopefully that saved you
00:31:09.200 some heartache. So, now that we've
00:31:10.559 covered some of the best practices on
00:31:12.799 creating tools and you've seen how to
00:31:15.440 add tools to your agents, let's go off
00:31:18.320 and run these different agents with the
00:31:21.120 different tools so you can see them in
00:31:22.480 action. And to start off, we're going to
00:31:24.240 start with Google search and then we're
00:31:25.520 going to test it again using the current
00:31:27.279 time so you can see it you can see it
00:31:28.799 working. So let's get this up and
00:31:30.159 running so we can work with Google
00:31:31.200 search. We're going to head over to our
00:31:32.559 terminal and start running it. So the
00:31:34.000 first thing we need to do is open up our
00:31:36.320 terminal. And what we want to do is make
00:31:38.640 sure two things are happening. One, you
00:31:40.480 want to make sure you've activated your
00:31:42.159 virtual environment. Head back to the
00:31:43.919 beginning of the video to check out
00:31:45.519 instructions for to do that. And the
00:31:47.519 second thing is you want to make sure
00:31:48.559 you change directory to the tool agent
00:31:51.039 folder. So this one right here. Once you
00:31:52.960 have that set up, you can run ad web and
00:31:55.760 this will once again spin up a website
00:31:58.320 that allows you to interact with your
00:32:00.000 agents. Now you can see that we have an
00:32:02.799 updated agent here which is the tool
00:32:04.559 agent. So I can say hey do you have any
00:32:08.159 news about Tesla this week? And what
00:32:11.120 this will do is go off search the
00:32:13.760 internet using the Google search tool.
00:32:16.080 So you'll see in just a second you can
00:32:18.000 see yeah right here. So you can see the
00:32:20.240 tool we called. So it's the Google
00:32:22.640 search and it looked up specifically
00:32:24.640 this query Tesla news this week. And
00:32:27.200 from there it generated a basically a
00:32:30.320 nice result that we can ask questions
00:32:31.919 about. So you can see like oh the stock
00:32:34.000 did this. Here's what happened for the
00:32:35.840 Q1 results. Basically everything that
00:32:37.919 happened this week in Tesla. And what's
00:32:39.760 so cool is you can dive into all the
00:32:42.240 different events that happened to see
00:32:43.919 what was going on under the hood. So per
00:32:45.919 usual, click on the event and you can
00:32:48.559 see the tool agent now has new
00:32:51.120 functionality. So the tool agent now has
00:32:53.120 access to the Google search tool. And
00:32:55.760 when you look inside of it, you can see
00:32:58.080 per usual, you can see the instructions
00:33:00.000 we gave it. And you can see the query we
00:33:02.480 passed in. And when you look at the
00:33:04.000 response, you can see when we scroll
00:33:06.559 down just a little bit, you can see, oh,
00:33:09.360 it went off and searched all these
00:33:11.120 different websites for us. scraped all
00:33:12.960 the information from a Google search and
00:33:14.799 then gave it back to us. So, this is
00:33:16.320 when we're starting to see the power of
00:33:17.840 using tools inside of our agents. So,
00:33:20.000 this one worked pretty well. What we're
00:33:21.679 going to do now, I'm going to close out
00:33:22.960 of this and we are going to change up
00:33:25.200 the agent to start using the get current
00:33:27.440 time tool. So, you can see this one in
00:33:29.519 action. So, we're going to do get
00:33:30.880 current time. We are going to keep this
00:33:33.279 one just how it is. And now what we're
00:33:35.200 going to do, close the kill the server.
00:33:37.760 Try it again. ADK web. This will
00:33:40.159 recreate the server once again. So we
00:33:42.000 can check out our website. We'll open it
00:33:44.080 up. So we still have a tool agent. And
00:33:45.919 now we can say, hey, what is the current
00:33:50.240 time? And when we run this one, we'll
00:33:52.799 see a different type of function
00:33:54.640 calling. So the last one was a built-in
00:33:56.159 tool call. And now what we're doing is
00:33:58.159 we're triggering our custom tools. So
00:34:00.559 you can see we sent an event to get
00:34:02.960 current time and then we got back a
00:34:04.480 result from get current time. And the
00:34:06.720 final answer was formatted and sent back
00:34:08.560 to us. So all around super super nice,
00:34:11.119 super helpful. And per usual, we can
00:34:13.119 check out the events to see exactly what
00:34:14.879 went down. So we can see in the first
00:34:17.679 event, our tool agent now has new tools,
00:34:20.639 in this case, get current time. And we
00:34:22.719 can look at the request. We can see our
00:34:24.719 updated request. We can see the message
00:34:26.560 we sent over. And then we can check out
00:34:28.320 the response. And this time you can say,
00:34:30.079 hey, I'd like to do a function call to
00:34:32.560 what function? Oh, the get current time
00:34:34.719 function, the one that we just passed
00:34:36.000 in. And we can step our way through the
00:34:38.639 different events to see what's going on.
00:34:40.560 So in the second event, you can see
00:34:42.560 we're waiting for tool calls to happen.
00:34:44.639 So this is basically yeah, it's making a
00:34:46.560 call. And then the third event, you can
00:34:48.320 see, okay, I got the result from current
00:34:50.480 time. And you can see here what is the
00:34:52.560 final result. So yeah, that is tool
00:34:54.560 calling in a nutshell. And don't worry,
00:34:56.239 we're going to be adding in a lot more
00:34:57.920 tools throughout the rest of this
00:35:00.240 examples inside this crash course. But
00:35:02.480 to start off, I just want you guys to
00:35:03.920 see the basics so you can see how
00:35:05.680 everything works together, how to use
00:35:07.040 built-in tools, custom tools, everything
00:35:08.560 else. So, you now have leveled up as an
00:35:10.480 ADK developer. And now we're going to
00:35:13.040 move over to example number three, where
00:35:15.200 you're going to learn how you can bring
00:35:16.720 in OpenAI models and models from Claude
00:35:19.760 inside of ADK. So, let's hop over to
00:35:21.680 example number three. Welcome to example
00:35:23.760 number three, where you're going to
00:35:25.119 learn how to connect your ADK agents to
00:35:27.680 other models like OpenAI and Claude. And
00:35:30.880 in this example, we're going to first
00:35:33.119 walk through a few of the core
00:35:34.400 technologies you need to support this
00:35:36.079 functionality. So, we're going to head
00:35:38.160 over to light LLM and open router to
00:35:40.960 understand what they are and how we need
00:35:42.400 to use them. From there, we're going to
00:35:43.920 dive into the code so you can see how
00:35:45.599 you can configure everything up. And
00:35:47.359 then finally, we're going to run the
00:35:49.040 agents using these new models so you can
00:35:51.119 see how everything works together. So,
00:35:52.720 let's go ahead and head over to looking
00:35:54.960 at Open Router and Light LLM. All right.
00:35:56.880 So, the first technology we're going to
00:35:58.480 be using to connect our ADK agents to
00:36:00.960 all sorts of different models is Light
00:36:02.960 LLM. And in case you haven't heard of
00:36:04.880 Light LM before, it is a free library
00:36:07.440 that you can use that handles all the
00:36:09.760 complexities of working with different
00:36:11.520 models like OpenAI, Claude, Llama. It
00:36:14.960 handles all the complexities with each
00:36:16.400 one of them and gives us one nice
00:36:18.000 library to interface with all of these
00:36:20.079 different models. So, here's just a
00:36:22.320 quick example of what it looks like to
00:36:24.320 work with Light LLM. So as you can see
00:36:27.119 like I said it is a package but under
00:36:29.680 the hood all it's doing is you pass in a
00:36:32.720 model. So OpenAI claude whatever model
00:36:35.200 you want to use you pass it in right
00:36:36.640 here and then you just pass in a
00:36:38.400 message. That's basically how light LLM
00:36:40.880 works and under the hood it is handling
00:36:43.040 all the different connections and all
00:36:44.960 the different types and functions to
00:36:46.560 make your life as easy as possible. So
00:36:48.400 that's the first technology we're going
00:36:49.599 to be using cuz ADK actually imports
00:36:52.000 light LLM. you're going to see in just a
00:36:53.359 second and it makes it even easier than
00:36:55.040 what you see right here. The next
00:36:56.480 technology we're going to use is Open
00:36:58.720 Router. Now, Open Router is a tool that
00:37:02.320 allows us to purchase tokens that can be
00:37:05.200 used for any model. So, it is basically
00:37:08.160 one tool that allows you to connect to
00:37:10.480 OpenAI Claude and these are actually to
00:37:13.119 make requests over to the different
00:37:14.880 servers. So, you can look up any model
00:37:16.960 that you want. So, we can look up OpenAI
00:37:19.119 04 Mini and you can see, yep, I have
00:37:21.680 access to this model. Here's some
00:37:23.839 information about this model. It is
00:37:26.320 currently working. And here's how fast
00:37:28.079 we're getting for tokens per second
00:37:29.920 right now. And it carries some cost.
00:37:31.839 Now, Open Router is not a free tool. It
00:37:34.480 does cost money to use. And what you can
00:37:37.119 notice whenever you sign up for an Open
00:37:38.880 Router account because you need to do
00:37:40.240 it. So, you'll just head over to Open
00:37:41.760 Router, sign in, and what you'll do is
00:37:44.320 you will buy credits. And whenever you
00:37:46.480 buy credits, there's like a 3% or 5%
00:37:49.760 increase on the cost to use credits. And
00:37:52.640 outside of that, you can just use these
00:37:54.560 tokens and credits to make requests to
00:37:56.800 Gemini, OpenAI, Claude, whatever you
00:37:59.359 want to do. So, make sure you go ahead
00:38:01.359 and add in some credits here. So, just
00:38:03.359 add credits. Once you're done, what
00:38:05.119 you'll do is you will create an API key.
00:38:07.760 This API key is going to allow you to
00:38:10.079 have one key that you can use to access
00:38:12.800 every model which is the beauty of using
00:38:14.800 open router. So what we can do is click
00:38:17.440 create key and we will call this ADK
00:38:20.480 crash course and we'll click create. And
00:38:23.359 now we will get an API key. So copy this
00:38:25.920 API key and you will want to head back
00:38:28.640 to your code and we are in project
00:38:31.599 number three. So you'll want to go down
00:38:33.440 to yourv and you will paste in this open
00:38:36.800 router key. And that's all you need to
00:38:38.720 do in order to get things up and
00:38:40.400 running. So now that we've covered the
00:38:41.839 core technologies and we have you a open
00:38:44.400 router key, let's go in and actually
00:38:46.640 look at the agent so you can see what we
00:38:48.960 need to do in order to start
00:38:50.160 communicating with these different
00:38:51.359 models. So let's hop over to the agent.
00:38:52.960 All right, so we just opened up our
00:38:54.560 agent.py that's using light lm. So I
00:38:57.040 want to cover a few of the core changes
00:38:59.200 that we're making in order to start
00:39:01.280 working with other models. So first
00:39:03.520 things first, we need to make a import
00:39:06.640 to use light LLM. And we can see we're
00:39:09.440 importing this from Google ADK. And then
00:39:12.400 specifically when it comes to the model
00:39:13.839 we want to use, we are using light LLM
00:39:15.760 because light LLM is one interface that
00:39:18.079 allows us to communicate with all the
00:39:20.480 different model providers out there.
00:39:22.160 Now, when it comes to using light LLM,
00:39:24.800 there's pretty much for most
00:39:26.880 technologies and models out there, you
00:39:28.640 only need to provide two pieces of
00:39:30.560 information. The model and the API key.
00:39:33.599 So, let's look at the model first. When
00:39:35.599 working with light LLM, what you need to
00:39:37.680 do is first define the provider. So,
00:39:40.560 since we are using open router, we need
00:39:42.960 to define the provider first. So, open
00:39:44.960 router check. The next piece of
00:39:46.720 information we need to define is the
00:39:49.359 model family. So in our case, we're
00:39:51.760 wanting to check out OpenAI. So we want
00:39:53.760 to put OpenAI here. If we were wanting
00:39:55.520 to use Claude, we would put Anthropic
00:39:57.680 here. And then once you're finally done,
00:39:59.760 you want to put in the specific model
00:40:02.400 that you're using. So in this case, what
00:40:04.320 we're saying is, hey, I would like to
00:40:05.839 use the new model from GPT 4.1. And
00:40:08.720 we're wrapping it all inside of this
00:40:10.720 class. And what's so nice is all we have
00:40:13.520 to do is pass this model we create into
00:40:16.480 our agent. And that's all we need to do
00:40:18.079 to get it to work. Now the other piece
00:40:19.839 of information that you'll notice in
00:40:21.200 here is we are saying hey I would like
00:40:23.839 to look at my operating system and I
00:40:26.160 would like to get a specific environment
00:40:28.160 variable. In this case I would like to
00:40:29.920 get the open router API key. So if you
00:40:32.720 look in thev file that we created just a
00:40:34.880 second ago that's exactly what we're
00:40:36.720 doing. We're just pulling out this API
00:40:38.880 key to use in our agent. Great. So let's
00:40:41.680 look at what we're trying to do with
00:40:43.040 this new model so we can run it and see
00:40:45.040 in action. So in our case, we are
00:40:46.880 creating a dad joke agent. So dad joke,
00:40:49.760 dad joke. And we're saying, hey, you are
00:40:52.800 a helpful assistant that tells dad
00:40:54.480 jokes. Please only use the tool get dad
00:40:57.280 jokes to tell a joke. So here's the
00:40:59.200 custom function that we've created. It's
00:41:01.440 a list of jokes. Just basically like
00:41:04.160 knock-knock jokes. And we're saying,
00:41:05.839 hey, please randomly pick a joke from
00:41:09.200 this list. That's all it's doing. So
00:41:11.040 what we can do is start running this
00:41:13.280 agent so you can see it in action. So
00:41:15.359 per usual, we are going to open up our
00:41:17.920 terminal. We need to change directory to
00:41:20.480 the proper project. So we're in example
00:41:22.560 number three and then we can run adk
00:41:25.280 web. ADK web will spin up our terminal
00:41:28.240 or basically our web interface so that
00:41:30.079 we can check out our new agent in
00:41:32.560 action. So you can see great we have dad
00:41:34.880 joke agent and we can say hey please
00:41:38.160 tell me a joke and this will go off and
00:41:41.760 do exactly what we did in the previous
00:41:43.200 tool calls where we went off and made a
00:41:45.280 a request to get the dad joke. We got
00:41:47.040 the dad joke back and then finally it
00:41:49.280 returned the dad joke from our tool
00:41:51.200 call. So all around this is awesome. And
00:41:52.640 the crazy part is we're not using Gemini
00:41:54.800 for this. We're using Open AI. And as a
00:41:57.760 quick extra note because I want to be as
00:41:59.920 helpful as possible for you guys. If you
00:42:02.240 want to see all the different compatible
00:42:04.480 models for open router, I have a link
00:42:06.880 that you can see in the source code. So,
00:42:08.640 let me show this for you real fast. But
00:42:10.800 this link right here will take you to
00:42:13.200 light LLM docs. So, you can see how to
00:42:15.440 connect to Open Router. And here's a
00:42:17.440 list of some of the most popular models
00:42:19.760 you can chat with. So, you can see
00:42:21.440 everything from OpenAI. You can see we
00:42:23.760 have our cloud models down here. But if
00:42:26.480 you want to check out the full list of
00:42:28.160 compatible Open Router models, you can
00:42:30.319 click here in the docs and it'll take
00:42:32.480 you over to Open Router. We looked at
00:42:34.000 this earlier, but you can type in any
00:42:36.560 model you want. So, if you wanted to use
00:42:38.640 something from llama, you can type in,
00:42:41.520 let's just say we wanted to do llama 4.
00:42:44.880 So, what we can do here is you can see,
00:42:47.119 okay, cool. I'd like to use this one. So
00:42:49.920 if we wanted to use this model, what we
00:42:52.240 would type in is we would go okay, I
00:42:54.800 would like to use open router open
00:42:58.000 router for slash and then I would type
00:43:00.240 in meta llama/ the name of the model. So
00:43:03.760 just know before you use any of these
00:43:05.599 models right here, you always need to
00:43:07.839 add open router before it to properly
00:43:09.920 use it in your agents. Yeah, you have
00:43:11.680 access to all models that are available.
00:43:14.000 And if you just want to experiment, you
00:43:16.640 can click on the rankings in Open Router
00:43:18.400 and see what models are absolutely
00:43:20.480 crushing it. So you can try them out for
00:43:22.640 your own. So yeah, all around Light LLM
00:43:25.040 plus open router is a huge cheat code
00:43:26.880 when trying to interface with all sorts
00:43:28.880 of models to really expand the
00:43:30.640 capabilities of working inside of agent
00:43:32.800 development kit. So yeah, that's a wrap
00:43:34.800 for example number three. And now we're
00:43:36.640 going to move over to our next examples
00:43:39.119 which is focused on structure outputs to
00:43:41.119 make sure our agents generate the proper
00:43:43.440 type of data we wanted to spit out. So
00:43:45.440 let's go ahead and hop over to example
00:43:46.880 number four. Hey guys and welcome to
00:43:48.560 example number four where we are going
00:43:50.640 to look at the different ways we can
00:43:52.960 make sure our agents generate the proper
00:43:55.599 structured data. And this is going to be
00:43:57.839 super important as you build larger and
00:44:00.000 larger agent workflows because you want
00:44:02.079 to make sure agent A is producing the
00:44:04.160 correct information in the right format
00:44:05.680 for agent B or so you can take the
00:44:07.920 information from agent A and pass it
00:44:09.680 over to an API, another tool or whatever
00:44:11.839 you want to do. So structured outputs
00:44:13.280 are super important. So what we're going
00:44:15.040 to do is first look at the docs to see
00:44:16.720 what options we have available to us.
00:44:18.800 And then second, we're going to look at
00:44:20.160 a pre-built agent I've created for you
00:44:21.920 guys so you can see the structured
00:44:23.920 outputs in action and see what we have
00:44:26.240 to do to get it up and running. And then
00:44:27.920 finally, we're going to run the code so
00:44:29.440 you can see everything in action. So
00:44:30.560 let's go ahead and check out the docs.
00:44:32.160 Okay, guys. So let's dive into the
00:44:34.400 structuring data docs when it comes to
00:44:36.599 ADK. Now, we're going to walk through
00:44:38.720 the three different options real fast
00:44:40.240 and I'll give you my feedback on all of
00:44:42.000 them and just to give you guys a brief
00:44:43.680 overview before we dive into the code
00:44:45.040 and see these guys in action. So the
00:44:47.440 first option you have is to define input
00:44:49.280 schema. I personally dislike this one
00:44:52.079 because it's very easy to fail. For
00:44:54.480 example, if a the previous agent is
00:44:57.200 saying, "Hey, I need to give you this
00:45:00.000 information." And we say, "Cool. I'm
00:45:02.079 expecting this other type of
00:45:03.520 information." Things are going to break.
00:45:04.880 So this one's a little bit too rigid. So
00:45:06.560 I usually try to stay away from this
00:45:08.000 one. But there is another format that
00:45:10.960 you're going to be using all the time,
00:45:12.560 which is going to be output schema. And
00:45:15.040 basically what output schema does is it
00:45:17.119 says okay AI agent I would like you to
00:45:20.240 create and generate an output that looks
00:45:22.960 like a specific class. So for example
00:45:25.520 they have a great demo down here where
00:45:27.760 you can say okay agent I would like you
00:45:31.280 to please generate a output in the form
00:45:34.480 of a capital output. So this is a class
00:45:37.119 we define and you can see up here when
00:45:40.000 it comes to the model it is a base model
00:45:42.560 imported from pedantic. That's exactly
00:45:44.160 what the doc said. And what you can see
00:45:46.160 inside of it is we go, "Oh, okay. I want
00:45:48.640 this agent to return a JSON object that
00:45:51.920 has a single property in inside of it, a
00:45:54.480 capital. This capital will have a
00:45:56.880 string." And I know that basically some
00:45:59.920 additional information to help the agent
00:46:01.280 figure out what it should put here is a
00:46:03.440 description of it. So I can see oh okay
00:46:05.920 the agent is going to whenever we ask it
00:46:08.319 a question return a object that has a
00:46:10.800 capital and the capital always needs to
00:46:13.040 be the capital of a country. So that's
00:46:15.520 basically output schema in a nutshell.
00:46:18.720 There is one quick constraint. So this
00:46:20.319 is something you need to know before
00:46:21.760 using this in the wild. It is you cannot
00:46:24.400 use output schema when using tools or
00:46:27.760 transferring information to other
00:46:29.119 agents. So later on, don't worry. What
00:46:31.680 we'll do is we'll have agent one, we'll
00:46:34.160 just have agent one do all the complex
00:46:35.920 thinking, pass the raw results over to
00:46:37.599 agent two, and then agent 2 will be the
00:46:39.839 one responsible for making sure the
00:46:41.440 output schema is met. Okay. Now, here's
00:46:43.599 the final thing. When it comes to output
00:46:45.839 key, this is a special name we can give
00:46:49.119 to say, hey, I would like to store all
00:46:51.520 the information you generate from here
00:46:53.839 to a specific spot in state. Now, we
00:46:56.160 haven't talked about state yet. We will
00:46:57.599 more in the next section, but just think
00:46:59.200 of state as memory that all of your
00:47:01.200 agents can access. So what you can say
00:47:03.680 is, okay, great. This agent is going to
00:47:06.800 find the capital. It's going to make
00:47:08.800 sure the output looks like this. It's
00:47:10.880 going to be an object that stores a
00:47:12.480 capital name. And what it's going to do
00:47:14.400 is it's going to save the capital to
00:47:17.920 state. So what we could do is eventually
00:47:20.400 look up state.found capital. And when we
00:47:23.920 look up the found capital, we will be
00:47:25.760 able to see the result that was
00:47:27.119 generated here. And our other agents
00:47:28.640 will be able to access this information.
00:47:30.319 And this is one of the best ways to
00:47:32.160 help, you know, agent one generate
00:47:34.160 information and agent two look up what
00:47:36.480 the previous agent did use that
00:47:38.079 information for the next. So this is how
00:47:39.680 we get to basically start having one
00:47:42.000 shared area with all of our information
00:47:44.640 and all of our agents can access it. And
00:47:46.480 it's very structured so we make sure
00:47:48.560 that our agents always have access to
00:47:50.319 the information they need. So that was a
00:47:52.160 ton. So let's actually look at a real
00:47:53.839 world example so you can see this in
00:47:55.440 action. So let's hop over to the code.
00:47:57.119 Okay, so now we're in the code when it
00:47:58.720 comes to working with structured
00:47:59.920 outputs. And I promise a lot of those
00:48:01.359 initial concepts we talked about are
00:48:02.880 going to come together and make sense.
00:48:04.480 So as you saw earlier, there was a few
00:48:06.800 important things that we needed to add
00:48:09.200 to our agent to get structured outputs
00:48:11.920 working. The two most important ones
00:48:14.160 were output schema. So this is what's
00:48:16.400 going to define yes you need to return a
00:48:19.680 object of this class type and you can
00:48:22.160 see for this agent we defined our email
00:48:24.640 content up here. So just a quick bit of
00:48:26.800 background in this example we're trying
00:48:28.240 to say hey agent it is your job to take
00:48:30.240 in some text I give you and convert it
00:48:32.240 into an email that has two options or
00:48:34.720 two properties. It has to have a subject
00:48:36.400 line and it has to have a body. So every
00:48:39.359 time we give the agent information it
00:48:41.520 will always return this type of
00:48:43.760 structured data. Now, so a few other
00:48:46.400 things that are important to note before
00:48:48.000 we dive too deep into the instructions.
00:48:50.400 You must for best results when working
00:48:52.720 with agents. Whenever you're using an
00:48:55.119 output schema like this, you need to do
00:48:58.400 a good job of defining what the schema
00:49:01.680 is beforehand. So, for example, in the
00:49:03.839 instructions, you need to do a good job
00:49:05.839 of saying, "Yep, I would like you to
00:49:08.240 return JSON matching this structure
00:49:10.880 subject and body." That's exactly what
00:49:12.720 we defined up here, but we need to put
00:49:14.559 it in our instructions as well. The
00:49:16.319 reason why we need to do this is if we
00:49:18.079 don't tell the agent what type of data
00:49:20.559 it needs to return whenever the agent
00:49:22.800 generates its draft of like, yeah, I
00:49:24.880 think I need to return this information.
00:49:26.880 Well, whenever it gets to the final step
00:49:28.480 and it goes, okay, here's my raw data.
00:49:30.400 I'm going to try and, you know,
00:49:31.680 basically change it to fit this output
00:49:33.200 schema. If it doesn't able, if it's not
00:49:35.520 able to make that match, things will
00:49:36.960 just fail and it's going to say, hey, I
00:49:38.160 was unable to generate this output
00:49:39.599 schema and things just crash. So the
00:49:41.359 better job you can do when defining the
00:49:43.200 output schema in here, the more likely
00:49:44.800 your agents will do at succeeding at
00:49:46.720 generating this this information
00:49:48.079 properly. Okay, cool. So that was super
00:49:50.480 important to note. Now let's just
00:49:51.839 quickly look at the instructions and
00:49:53.040 then we're going to run it so you can
00:49:54.319 see how I was talking about state
00:49:55.839 earlier with output keys. Yes, state
00:49:58.000 with output keys. You're going to see
00:49:59.520 how the email we generate actually gets
00:50:01.520 saved to state using the email as the
00:50:04.319 word the keyword and you're going to see
00:50:05.839 the email it generates as the value. So,
00:50:07.520 you'll see this in action in just a
00:50:08.640 second, but let's quickly look at the
00:50:10.400 instructions so you can see exactly what
00:50:11.680 we're doing. We're saying, "Hey, you are
00:50:13.440 an email generation assistant. You
00:50:15.440 always write professional emails based
00:50:17.040 on the user's request, and here are some
00:50:19.119 guidelines when you're writing a email.
00:50:21.359 You need to make sure that you always
00:50:22.800 create a concise and relevant subject
00:50:24.720 line. And then the body of the email
00:50:26.960 needs to be pretty professional with a
00:50:28.720 greeting. And then finally, what you
00:50:30.720 want to do is make sure the tone is
00:50:32.880 businessfriendly, formal, keep it
00:50:34.640 concise, but complete. And then as we
00:50:36.400 said earlier as a must, please, please,
00:50:38.720 please make sure you include the JSON
00:50:40.640 structure for best results. Okay, great.
00:50:43.119 That's everything that we need to do. So
00:50:45.200 let's run the agent so we can see this
00:50:47.440 in action. So we are in the proper
00:50:49.599 folder structured outputs. We have our
00:50:51.920 virtual environment created. So we can
00:50:54.000 now run ADK web. This is going to spin
00:50:56.240 up our website that you normally see.
00:50:57.839 And I'm super excited to show you guys
00:50:59.280 this in action because as you build your
00:51:01.680 own agents, you will see quickly how
00:51:04.160 powerful and how important this is in
00:51:06.240 order to build bigger, more complex
00:51:08.000 workflows. So we can say, "Hey, please
00:51:11.200 write a email to my wife
00:51:16.520 Carly to see if she is available for
00:51:21.240 coffee tomorrow morning." So what it's
00:51:24.480 going to do is take in that input that
00:51:26.800 we gave it and you can see the agent
00:51:29.440 returned the two pieces of information
00:51:31.280 we wanted the subject it also returned
00:51:33.920 the body cuz that's exactly what we
00:51:35.359 defined in the schema. Now digging even
00:51:38.000 deeper you can see inside a state we now
00:51:41.760 are saving the email we generated in the
00:51:44.880 exact format that we said. So in our
00:51:47.040 case, we said, "Hey, I would like you to
00:51:48.960 save the email using the key email and
00:51:52.480 then the body like whatever response you
00:51:54.319 generate, you need to save it in here."
00:51:56.319 And the reason we can see this is
00:51:57.920 because if you hop back over here at our
00:52:00.480 agent, you can see, yep, the output key
00:52:02.720 was email. It's right here. And then the
00:52:05.119 generated result is spit out right here.
00:52:07.680 Now, just to show you guys something
00:52:08.880 else is if we were to write another
00:52:11.359 email, it will override this state. So
00:52:13.520 you can say great see great we'll say
00:52:17.680 write another email to see if Nate is
00:52:22.319 free for pickle
00:52:24.119 ball tomorrow night. Now this will
00:52:27.599 create another email and it will save
00:52:30.079 the result once again to state. So you
00:52:32.400 can see new subject line new body but
00:52:35.359 it's all saved under the same key. So
00:52:37.359 that is working with structured outputs
00:52:39.599 in a nutshell to where you now have
00:52:41.359 total control of making sure your agents
00:52:43.440 always generate the proper output schema
00:52:45.599 and save the information exactly where
00:52:47.680 you want in state so other agents can
00:52:49.599 use it or you can pass that information
00:52:51.359 over to other tools and APIs. So that
00:52:53.200 one was a little bit more complex.
00:52:54.559 Hopefully the explanation made sense.
00:52:56.720 And now we're going to move over towards
00:52:59.359 our next example where we are going to
00:53:02.000 start to look at some of the core
00:53:03.640 underlying pieces and concepts inside of
00:53:06.559 ADK which are going to be session and
00:53:08.800 memory. So let's hop over to example
00:53:10.880 number five. So welcome to example
00:53:13.040 number five where we're now going to
00:53:14.800 look at some of the core components you
00:53:16.960 need to use in order to run your agents.
00:53:19.359 So in this example we're going to look
00:53:21.359 at sessions, state, and runners. And to
00:53:24.559 make this all super easy to digest, what
00:53:26.559 we're going to do is break this up into
00:53:28.000 three phases. Part one, we're going to
00:53:29.760 hop over to a whiteboard so you can see
00:53:31.760 how all these core components work
00:53:33.760 together and what they do so you have a
00:53:35.440 good understanding of it. And once we
00:53:36.800 have a highle understanding of what
00:53:38.480 these components are, we're going to
00:53:39.760 dive into code in phase two where you're
00:53:42.079 going to see, okay, I understand what a
00:53:43.760 runner is now, but how do I actually
00:53:45.359 create it in code? Well, that's what
00:53:46.640 we're going to be doing in phase two.
00:53:48.079 And then part three, we're going to kick
00:53:49.680 off the code that we run so you can see
00:53:51.760 how it actually works and so you can
00:53:53.599 see, you know, some of the outputs of
00:53:55.440 everything running together. So let's go
00:53:57.040 ahead and hop over to the whiteboard so
00:53:58.720 we can deep dive into some of these core
00:54:00.720 components. So welcome to the whiteboard
00:54:02.400 time, guys, where we're going to start
00:54:03.839 diving deep into understanding what is
00:54:05.599 session, state, and runners and how do
00:54:07.359 they all work together. And the good
00:54:09.040 news is you've already been using each
00:54:11.200 one of these different technologies and
00:54:12.720 core concepts whenever you've been
00:54:14.480 running ADK web. So far, every time we
00:54:16.640 run ADK web, it handled all the
00:54:18.880 complexity of spinning up all the
00:54:20.480 back-end code that created sessions for
00:54:22.640 us. So, as you can see, you know, every
00:54:24.640 time we were working and chatting with
00:54:26.079 our agent, it created a unique session
00:54:27.680 for us. We'll explain that more in just
00:54:29.599 a little bit. You can also see that it
00:54:31.359 had state for us. And then every time we
00:54:33.680 were chatting with our agent, we were
00:54:36.000 really passing our inputs and questions
00:54:38.079 over to a runner who was connecting
00:54:40.160 everything together for us. So, enough
00:54:42.240 like highle talk. Let's actually see
00:54:44.400 what these different components are. And
00:54:46.240 what I would like to do first is talk
00:54:48.160 about sessions. Once we talk about
00:54:49.839 sessions, we're then going to talk about
00:54:51.440 runners. So you can see how these
00:54:53.040 different core concepts work together.
00:54:54.880 Okay. So a session inside of ADK is
00:54:58.640 nothing more than really two major
00:55:01.119 pieces of information. A session has a
00:55:04.400 state. So a state is where you can store
00:55:06.640 all sorts of information in a dictionary
00:55:09.280 where you have keys and values. So keys
00:55:11.680 could be like username and the value of
00:55:13.839 username would be Brandon. So that's
00:55:16.000 what we're storing in state. Outside of
00:55:17.760 that, inside of a session, we have
00:55:19.839 events. And think of events normally
00:55:22.480 just like a message history between us
00:55:24.800 and the agent. But there's actually a
00:55:27.119 little bit more to it than just
00:55:28.599 messages. There is also tool calling and
00:55:31.440 agent responses. And the event history
00:55:34.480 is just a list of everything that
00:55:36.800 happens between us and the agents. And
00:55:39.119 it's a nice way to store all the
00:55:40.960 information so that every time we add a
00:55:43.599 new message to the bottom, it can look
00:55:45.520 back at everything we said so far and
00:55:47.200 understand, oh, okay, I see we've been
00:55:49.440 talking about this topic. So, if you ask
00:55:51.680 for more information, you want me to
00:55:53.280 provide more information on the
00:55:54.559 conversation we were just talking about.
00:55:55.920 So, sessions at a high level so far,
00:55:58.079 state and events where events are
00:56:00.079 messages between us and the agent.
00:56:02.799 Outside of that, sessions have a few
00:56:04.880 additional pieces of information.
00:56:07.200 sessions have ids, app names, user ID,
00:56:10.480 and last update time. So, let's talk
00:56:12.480 about what each one of these is at a
00:56:13.839 high level really quickly. So, as you
00:56:15.839 begin to build larger agent workflows,
00:56:18.960 you eventually we want to be able to
00:56:21.119 look up sessions. So, you'll want to
00:56:23.040 say, "Oh, for user Bob, I want to see
00:56:25.440 all the different conversations he's had
00:56:28.000 between him and the agents that we've
00:56:30.720 created." And in order to look that up,
00:56:32.640 what we'd want to do is go, "Oh, okay.
00:56:34.799 I'm working in this app and I'm trying
00:56:36.960 to look up the conversation that user
00:56:39.280 Bob had with it. Oh, okay. By looking up
00:56:41.920 that information, I can see Bob was in
00:56:44.720 session 123. So now I can easily pull
00:56:47.599 out that session and allow Bob to
00:56:49.520 continue to chat with that session. So
00:56:52.000 think of think of sessions really as
00:56:53.839 just a stateful chat history. That is
00:56:56.079 the best way to think of sessions. Okay,
00:56:58.720 so that's sessions at a high level. Now
00:57:00.880 to uh add in a little bit of complexity
00:57:03.119 there are multiple types of sessions. So
00:57:05.839 there is in-memory session which is
00:57:08.160 where we are saving all the conversation
00:57:10.720 histories that we're having with each
00:57:12.319 one of our agents and we're saving in
00:57:14.640 memory which means as soon as we close
00:57:17.119 out of the application everything in
00:57:18.640 memory is gone and we lose access to all
00:57:21.119 the conversations that we had. The next
00:57:22.960 option is to do a database session and
00:57:24.960 we're going to do database session in
00:57:26.400 example six the example right after
00:57:28.000 this. But basically, every time we have
00:57:30.079 a conversation with our agent, we're
00:57:31.839 going to store it to a database, which
00:57:33.520 is nice because when we close out of the
00:57:34.960 application, all the information is
00:57:36.400 still saved. And when we reload the
00:57:38.720 application, it'll go, "Oh, great. I can
00:57:40.480 pull out all the existing conversations
00:57:42.480 between Bob, all the our other users, I
00:57:44.720 can pull them out." And that way,
00:57:45.920 whenever they want to continue the
00:57:47.119 conversation, they can. Then what the
00:57:49.920 third option you can do is to save these
00:57:52.880 sessions to Vertex AI. Vertex AI is
00:57:56.079 Google Cloud's AI platform. It is
00:57:58.480 amazing. I actually have an entire
00:58:00.240 tutorial teaching you how to deploy your
00:58:01.920 agents to App Engine on Vert.Ex AI. But
00:58:05.040 just know if you want to store your
00:58:06.400 sessions in the cloud and not on your
00:58:08.160 local computer, Vert.Ex AI is the
00:58:10.160 easiest way to do it. It's out of the
00:58:11.760 scope for this tutorial. And but I just
00:58:13.920 want you to know you have multiple
00:58:15.040 options. Save it in memory to where it
00:58:16.799 goes away. Save it to a database to
00:58:18.480 where you get to keep it on your local
00:58:19.599 computer or option three, save it to the
00:58:21.440 cloud with Vert.Ex AI. Okay, great. So
00:58:24.480 we've seen sessions at a high level. I
00:58:27.040 want to show you what a code snippet
00:58:28.640 looks like of creating a session. So, as
00:58:31.040 we decided just a second ago, you have
00:58:33.280 to pick where do you want to save your
00:58:35.040 sessions. So, we are going to import our
00:58:37.440 sessions and use the in-memory one cuz
00:58:39.359 we're not trying to connect it to
00:58:40.319 anywhere fancy right now. So, we're
00:58:41.760 going to say all right, I would like a
00:58:43.440 in-memory session. And then what we can
00:58:45.760 do from there is go I would like to
00:58:47.760 create a session because I want to be
00:58:50.480 able in this case my example user to be
00:58:53.520 able to begin talking with my agents.
00:58:56.319 And then you can pass in some additional
00:58:57.839 information like the app name. It is
00:58:59.760 required but just know you know we're
00:59:02.000 we're not really building apps right
00:59:03.200 now. We're just mostly focused on
00:59:04.480 talking with our agents. So yeah just
00:59:06.079 know you have to give an app name. You
00:59:07.599 have to give it a user ID. And then from
00:59:09.920 there the other option you have is to
00:59:11.920 give state. State is optional, but this
00:59:14.160 is where you can pass in all sorts of
00:59:16.079 user preferences or whatever agentic
00:59:18.400 workflow you're building. It's usually
00:59:19.920 helpful to build pass in state to allow
00:59:21.760 the agent to have some additional
00:59:23.440 context instead of just the instructions
00:59:25.680 we give it. Okay. Then once you create a
00:59:28.640 session, what you can see is when you
00:59:31.040 log what's in the example session, you
00:59:33.680 can see it has all of the different
00:59:35.119 properties that we called out right
00:59:36.559 here. So we have an ID, the application
00:59:38.960 name, the user ID, state. We have events
00:59:41.920 which were nothing more than the events
00:59:44.480 between us and the agent, specifically
00:59:46.720 the messages, tool calls, and agent
00:59:49.119 responses. That's what you're going to
00:59:50.559 see inside the event list. And then
00:59:52.720 finally, every time we make a request,
00:59:54.240 it also updates the last update time. So
00:59:56.720 you can just see like, oh yeah, we've
00:59:57.839 been using this agent super recently, or
00:59:59.680 no, we haven't touched this agent in a
01:00:01.040 week. Okay, great. So that's session at
01:00:03.280 a high level. And just the core takeaway
01:00:05.359 from this is sessions are just stateful
01:00:07.520 message histories. That's the core thing
01:00:09.520 to take away from this. Okay, great. So
01:00:12.319 now we're going to hop over to well now
01:00:15.599 that I know what a session is, how do we
01:00:16.960 actually like get agents to run? Like
01:00:18.880 there's a lot of moving parts. How do
01:00:20.400 they all connect? Well, everything
01:00:22.640 connects inside of a runner. And a
01:00:24.400 runner is I'm going to walk you through
01:00:26.640 what you need to provide to a runner
01:00:28.079 first and then we're going to go through
01:00:29.200 an example life cycle. So a runner is
01:00:32.160 nothing more than a collection of two
01:00:34.960 pieces of information. Your agents and
01:00:37.920 your sessions. So let's walk through why
01:00:40.160 we have to put this in an agent or
01:00:41.920 inside of a runner. So inside of a
01:00:43.680 runner, we need to give it agents so
01:00:45.599 that the runner knows every time it gets
01:00:48.319 a request. Well, what agents do I have
01:00:50.480 available to take and handle this
01:00:52.160 request? For example, if we were working
01:00:54.720 with a frequently asked question agent,
01:00:57.680 well, we would see, oh, okay, I have a a
01:01:00.720 question and answer agent. So, every
01:01:02.559 time I get a request, I know I can give
01:01:04.319 it to that agent to to be the starting
01:01:06.319 point to handle answering the question.
01:01:08.400 Also, we need to have a session because,
01:01:10.799 as we just discussed a second ago, we
01:01:12.720 need to have somewhere to store our
01:01:14.160 message history and our state. So, these
01:01:16.240 are the core components that you need in
01:01:18.559 order to create a runner. So, let's walk
01:01:20.799 through a quick example of how us
01:01:23.440 chatting with the runner actually works
01:01:26.079 step by step. So, let's say going back
01:01:28.160 to our frequently asked question agent,
01:01:30.079 let's walk through it. So, let's say our
01:01:32.079 user says, "Hey, what is my name?" Or we
01:01:35.920 can say, "Hey, what is the return policy
01:01:38.880 for this business?" We'll go with that
01:01:40.319 example. Well, first thing that it's
01:01:42.160 going to do is the runner is going to
01:01:43.680 go, "Okay, you are user Brandon and I
01:01:47.440 can see you are asking this question."
01:01:49.200 So, first thing I'm going to do is look
01:01:51.359 through our session. I can see you have
01:01:53.280 a user ID of 1 2 3. So, I'm going to
01:01:56.000 look through all the sessions I have
01:01:57.920 available and I'm going to see, okay, I
01:01:59.760 see you have a message history and you
01:02:02.160 are currently have this state. Great.
01:02:04.559 From there, it's going to pass over all
01:02:06.880 the context it provides and finds to an
01:02:09.440 agent. And this FAQ agent is going to
01:02:12.160 go, okay, I can see user Brandon likes
01:02:14.960 these things. He's purchased these
01:02:16.640 products from us. And now that I'm
01:02:18.559 working with the frequently asked
01:02:19.920 question agent, I can now begin to
01:02:22.400 generate a response. And this agent is
01:02:24.559 going to go, okay, in my workflow, I am
01:02:26.799 a single agent. I don't have five sub
01:02:29.680 agents, something we'll talk later about
01:02:31.280 more later on, but I can see that I have
01:02:33.520 one agent. So I am now trying to figure
01:02:36.000 out which agent is going to handle this
01:02:37.599 response. And since there is only one
01:02:39.520 agent in here, I'm going to pass the
01:02:41.440 query you gave me plus all the session
01:02:44.079 information I have about you to the
01:02:46.319 agent who's responsible for handling
01:02:48.480 this request. In this case, there's only
01:02:50.160 one agent. So that's the agent that gets
01:02:51.839 picked. From there, that agent makes a
01:02:54.640 few extra calls. If we have tools
01:02:57.040 provided to the agent, the agent will go
01:02:58.960 off and maybe search the internet. It
01:03:00.799 might go off and search our database.
01:03:02.480 Whatever we need to do, it will make the
01:03:04.079 necessary tool calls. And then from
01:03:06.000 there it'll pass in an a request over to
01:03:09.280 our large language model. So Gemini. So
01:03:11.599 it's going to pass the results from the
01:03:12.880 tool call into the large language model
01:03:14.960 and go, "Oh, okay. I can see you were
01:03:17.359 trying to make a request about our
01:03:19.359 return policy. I can see you've ordered
01:03:21.520 this product. Yep. I looked it up. It
01:03:23.839 looks great. It looks like you can
01:03:25.039 return that item within 30 days and it's
01:03:27.920 only been 20. So you can return that
01:03:30.720 item." From there, what'll happen is on
01:03:34.079 the way back to the user, we will update
01:03:36.640 our session by adding in new events
01:03:39.200 because if you remember from above,
01:03:41.200 sessions have two pieces of information.
01:03:43.119 They have state and they have events.
01:03:45.440 And these events can also include the
01:03:47.839 agent response. So, we're going to add
01:03:49.599 in the agent response where we're going
01:03:51.280 to say, "Yep, you can return the item
01:03:53.760 you're talking about." So, that's us
01:03:56.000 updating session. And then finally, the
01:03:58.240 runner is going to spit back the result
01:04:00.720 to the user and say, "Yep, looks good.
01:04:02.960 You can return the item. Everything's
01:04:04.960 happy." So this is the core loop in a
01:04:07.119 nutshell of working with basically all
01:04:10.000 the core concepts we just talked about,
01:04:11.760 which are going to be runners, sessions,
01:04:14.799 and state. So hopefully that makes
01:04:16.720 sense. The core lesson here is sessions.
01:04:19.039 Just one more time, sessions are
01:04:20.319 stateful message histories and runner is
01:04:22.880 nothing more than just a combination of
01:04:24.720 all the raw ingredients needed to
01:04:27.359 generate responses for our users. And
01:04:29.839 when I say raw ingredients, just a list
01:04:31.520 of our agents and the current session
01:04:33.599 we're working with. It combines them
01:04:35.200 together to help generate intelligent
01:04:37.119 responses. So hopefully that all makes
01:04:39.520 sense. And don't worry, we're going to
01:04:41.039 dive into a code example next so you can
01:04:42.960 see all of these different core
01:04:44.559 components working together so you can
01:04:46.240 see them in action. So, let's go ahead
01:04:47.760 and hop over to the code so you can see
01:04:49.839 everything running. So, now it's time to
01:04:51.440 look at the code when it comes to
01:04:52.960 combining all of our session, state, and
01:04:54.799 runners into one area so we can begin to
01:04:57.039 chat with our agents. And the core
01:04:58.880 takeaway that I want you to have inside
01:05:01.039 of this code example is we are having to
01:05:03.920 build all the core functionality that
01:05:06.079 ADK web command normally handles for us.
01:05:08.960 We're having to build it here. And this
01:05:11.119 is super important as you want to go off
01:05:13.200 and create more complex agents where you
01:05:15.760 don't want to just chat with them inside
01:05:17.280 ADK web. Let's say you want to start
01:05:19.119 incorporating agents inside of your
01:05:21.559 applications. This is how you would go
01:05:23.599 about doing it where you would yourself
01:05:25.760 manage the memory, the sessions and the
01:05:28.400 runners. This is what you would be
01:05:29.680 responsible for doing in your own
01:05:31.119 applications. So let's go through this
01:05:32.720 part by part where I'm going to explain
01:05:34.400 everything that's happening so you can
01:05:36.240 you know hopefully master everything as
01:05:37.599 well. Okay. So what are we doing first?
01:05:39.920 Well, first thing we're going to do is
01:05:41.920 we are going to load our environment
01:05:43.520 variables. The reason why is inside of
01:05:46.880 all of our other projects, we would keep
01:05:49.359 our environment variables with our
01:05:50.960 agents. But now that we're managing
01:05:53.440 everything ourselves, we need to keep
01:05:55.520 our environment variables at the root
01:05:57.440 level of our folder because we're not
01:05:59.680 running ADK web, which is going to
01:06:01.119 handle and pull out all the environment
01:06:02.400 variables inside of our agents. The
01:06:03.920 environment variables now need to leave
01:06:05.760 live at the top level of our folders.
01:06:08.160 And per usual, our environment variables
01:06:10.000 just have our API key and everything
01:06:12.000 else that we need to make requests.
01:06:13.760 Okay, great. So now let's start looking
01:06:15.920 at some of the core concepts that we are
01:06:17.839 trying to do here. So the first thing
01:06:19.520 that we decided is we need to pick which
01:06:22.640 memory service we're going to use. We
01:06:24.559 can do database inmemory or vertex AI.
01:06:27.760 We just want to run everything locally
01:06:29.280 for this example so you can get a you
01:06:31.359 know a quick overview of seeing this in
01:06:32.799 action. So we're going to create an
01:06:34.799 in-memory service where the second we
01:06:36.960 close the application all of our
01:06:38.559 sessions disappear. Okay. The next thing
01:06:41.039 that we are going to do is we are going
01:06:43.680 to create initial state. As I said
01:06:46.079 earlier initial state is nothing more
01:06:48.319 than a dictionary. So you can see we are
01:06:50.400 creating a dictionary right here and we
01:06:52.400 are giving it two keys. We are giving it
01:06:54.799 a username and user preferences. These
01:06:57.359 are the two different keys we are
01:06:58.720 passing in our dictionary. So we can
01:07:00.880 ideally in this frequently asked
01:07:03.200 question agent called Brandonbot what we
01:07:06.160 can do is answer questions about
01:07:08.079 Brandon. That's what we're trying to do
01:07:09.440 here. So that's why we want to pass in
01:07:10.960 initial state. Great. So now we are
01:07:14.000 going to create a session. And if you
01:07:16.400 remember what you have to do is inside
01:07:18.640 of whatever memory service you pick, you
01:07:20.960 can then say I'd like to create a
01:07:22.480 session using this service, this session
01:07:24.880 service. So in our case, we need to
01:07:26.640 create a session and pass in all the
01:07:28.880 values necessary in order to create it.
01:07:31.039 You saw this just a second ago when we
01:07:32.640 were looking at the Google example, but
01:07:34.640 you can see we need to pass in the app
01:07:36.480 name. In our case, Brandonbot. From
01:07:38.720 there, we need to come up with a user
01:07:40.880 ID. We're just going to call it Brandon
01:07:42.640 Hancock. And then we need to pass in a
01:07:44.960 session ID. And we're just going to do
01:07:47.119 this right here which is called a
01:07:49.440 universal uniquely identifiable key
01:07:52.079 basically which is just it's just going
01:07:54.000 to make a super long random character
01:07:56.559 that you know are very unique. And then
01:07:58.720 finally what we're going to do in our
01:08:00.240 session is we are going to provide
01:08:01.680 initial state. So that's everything you
01:08:03.359 need to do to create a session. Awesome.
01:08:06.400 So now that we've created our session
01:08:08.079 what we're trying to do is if you
01:08:09.680 remember when it comes to raw
01:08:11.119 ingredients to making a runner there was
01:08:13.440 two. For a runner, we need to have in
01:08:16.080 our case, we need to have our agent and
01:08:18.479 then we need to have our session. So, we
01:08:20.640 just created our session check. And the
01:08:23.520 next thing we need to do is pass in our
01:08:25.759 agents. So, where the heck do our agents
01:08:27.759 live? Well, in our case, we've created a
01:08:30.719 folder where our questionans answering
01:08:33.198 agent lives. So, you can see it's all in
01:08:35.600 the same folder. And if you open up your
01:08:37.359 questionans answering agent folder, you
01:08:39.279 can see it looks just like the rest of
01:08:41.198 them. And if you open up agent.py, Pi,
01:08:43.279 you can see, hey, you are a helpful
01:08:45.920 assistant and the job of you as a
01:08:47.920 helpful assistant is just to answer
01:08:49.198 questions about the user's preferences.
01:08:51.439 And this is where we're starting to get
01:08:52.560 a little fancy because in order for you
01:08:55.040 to access state, you can use begin to
01:08:57.679 use it's called string interpolation,
01:09:00.479 which is really just a fancy word for
01:09:02.238 putting the key you want inside of
01:09:04.399 brackets. So going back, let's do a side
01:09:07.040 by side so you can see it. So inside of
01:09:10.319 our basic session right here you can see
01:09:13.198 in our initial state we had items such
01:09:16.000 as our basically our username and you
01:09:19.279 can see that right here we can access
01:09:21.120 our username. So this is how you access
01:09:23.960 state inside of your agents. You just
01:09:27.040 pass in the key that you want from over
01:09:28.640 here and you can pass it in here. So
01:09:30.960 that is how you can access state inside
01:09:33.520 of your agents. super helpful and you're
01:09:35.279 going to do it a ton as you work more
01:09:36.960 and more with your agents. Okay, great.
01:09:38.560 So, now that we understand what the
01:09:39.679 agent can do, let's hop back over to our
01:09:42.960 runner because our runner was
01:09:44.880 responsible for taking in our agent that
01:09:47.439 I just showed you and responsible for
01:09:49.679 taking in our session service because
01:09:51.439 once it has those two core pieces of
01:09:53.279 information, we can now begin to ask
01:09:55.440 questions and send in messages to our
01:09:58.159 runner. Now in order to create a message
01:10:00.480 the raw way to do it inside of ADK is to
01:10:03.840 create a message that looks just like
01:10:05.280 this where you say hey I would like to
01:10:07.600 make a message and the way you do that
01:10:09.360 is through there's a library called
01:10:11.360 types. So from Google's generative AI
01:10:14.640 library that you have installed inside
01:10:17.280 of whenever we created our Python
01:10:19.080 environment. What we did is uh we
01:10:21.360 imported generative AI from Google. Now
01:10:23.679 what we can do is create a new piece of
01:10:25.280 content which is basically just a
01:10:26.480 message is the best way I like to think
01:10:27.600 of it. And with a content, you want to
01:10:29.520 pass in two pieces of information. The
01:10:31.760 role. So the role is going to be either
01:10:34.000 the user or the agent. So who's
01:10:36.719 responsible for sending this message,
01:10:38.080 role or user. And then from there, you
01:10:40.239 have parts. Think of parts just as the
01:10:42.560 raw piece of text that you want to pass
01:10:44.800 over to the agent as your query. In this
01:10:47.199 case, we're going to say, "Hey, what is
01:10:48.719 Brandon's favorite TV show?" This is the
01:10:50.640 message we want to send to the agent. So
01:10:53.120 what we can do is go all right now that
01:10:55.600 I have everything set up and ready to
01:10:57.760 run I can say all right runner I would
01:11:00.480 like you to run everything that I've
01:11:02.640 given you so far for the user ID and the
01:11:06.159 session ID and I would like you to
01:11:08.400 process this new message. From there the
01:11:11.520 runner is going to go off and process
01:11:15.280 everything that we just talked about in
01:11:16.640 the life cycle earlier where it's going
01:11:18.239 to look at the agents it has available.
01:11:20.000 It's going to pull information from
01:11:21.440 state by looking through our sessions.
01:11:23.440 Pass all that information over to the
01:11:25.280 relevant agent. There's only one this
01:11:26.960 time. So, it's just going to pass all
01:11:28.159 that context to that one agent. That
01:11:30.239 agent is then going to say, "Hey, do I
01:11:32.159 have any tools I can call?" Nope, I
01:11:33.840 don't. So, all I'm going to do is pass
01:11:36.320 all this information over to the Gemini
01:11:39.199 LLM. And the reason I say Gemini LLM is
01:11:41.760 because that's the only LLM that we have
01:11:43.360 attached to this agent. From there, it's
01:11:46.400 going to generate a response. And that
01:11:48.480 response is going to get saved as an
01:11:50.640 event to our session. So that's why we
01:11:53.040 are going to look through our session
01:11:55.040 and say, is this the final response from
01:11:57.600 this run? If it is, what I would like
01:11:59.840 you to do is please show me the content
01:12:02.880 from this final event so I can log it so
01:12:05.840 I can see it. And if you remember
01:12:07.600 earlier, every event, that's what we're
01:12:09.760 looking at. An event has content. That's
01:12:11.600 why this is like type.content. So, we're
01:12:13.920 just basically in short, in summary,
01:12:16.080 just looking for the message that was
01:12:18.480 responded and sent back by the agent.
01:12:20.960 So, that was a lot of talking. What I
01:12:23.120 would like to do is run this for you
01:12:24.719 guys so you can see it in action. So,
01:12:26.719 let's go ahead and run this. So, let's
01:12:28.640 clean things up. And a few things. First
01:12:30.960 off, we need to make sure that you are
01:12:32.640 in example number five and you do have
01:12:35.040 your current Python environment
01:12:36.880 activated. And what you can do now is
01:12:38.880 run Python and then run basic stateful
01:12:41.679 session. And if you remember what this
01:12:43.679 is trying to do is it's going to answer
01:12:45.440 the question, what is Brandon's favorite
01:12:47.199 TV show? And then we are going to log
01:12:49.679 two pieces of information. We are going
01:12:51.840 to first log the final response. Then we
01:12:55.040 are going to grab the current session
01:12:57.760 and we are going to show the session
01:12:59.600 state. That's what we're trying to do in
01:13:00.960 this quick example. So you can see
01:13:02.239 everything working together. So, it
01:13:04.000 takes a second to run and you can see
01:13:06.320 great, we created a new session with a
01:13:09.280 unique session ID and you can see it
01:13:11.920 answered the question super easily
01:13:13.360 because it looked through the state we
01:13:14.640 passed in. So, you can see, oh yeah,
01:13:16.159 Brandon's favorite TV show is Game of
01:13:18.000 Thrones currently re-watching it as we
01:13:19.840 speak. From there, what you can see is
01:13:22.080 we're doing a session event exploration
01:13:24.400 where we're just trying to look at the
01:13:25.520 final state. And once again, you can see
01:13:28.320 this initial state that we passed in.
01:13:30.000 You can see that we have access to all
01:13:31.679 of it right here. And this is how it was
01:13:33.840 able to answer the question of what is
01:13:35.600 Brandon's favorite TV show. So yeah,
01:13:38.080 that is sessions, state, and runners in
01:13:41.520 a nutshell. This was definitely a little
01:13:44.080 bit more codeheavy than running ADK web,
01:13:46.800 but these are the core components you
01:13:49.120 need to run your agents, especially if
01:13:51.199 you want to start adding them over to
01:13:52.880 your applications and you know, in order
01:13:55.440 to run your agents. So, what we're going
01:13:57.120 to look at next is we're going to head
01:13:58.640 over to example six. So, you can see how
01:14:00.880 we can connect up our sessions to a
01:14:03.679 database. So, it doesn't matter when we
01:14:05.199 close out of the application. When we
01:14:06.640 reopen it, we're going to have access to
01:14:08.000 all of our sessions. Let's go over to
01:14:10.000 example number six. Hey guys, and
01:14:11.840 welcome to example number six, where
01:14:13.920 you're going to learn how to store your
01:14:16.239 sessions and state to a local database
01:14:19.120 so that when you close out of your
01:14:20.640 application and reopen it, it's going to
01:14:22.880 be able to pull in all that existing
01:14:24.640 information and you're going to be able
01:14:25.679 to pick up the conversation right where
01:14:27.440 you left it off. And in this example,
01:14:29.120 we're going to break it down into two
01:14:30.560 parts. First, we're going to review the
01:14:32.719 entire code part by part so you can
01:14:34.960 understand exactly how we can pull out
01:14:36.960 existing sessions, how we can save
01:14:39.199 sessions to a database. We're going to
01:14:40.880 cover everything step by step. And then
01:14:42.560 part two, we're going to run the example
01:14:45.440 so you can see everything in action. And
01:14:47.040 this is by far one of my favorite
01:14:48.960 examples in the whole crash course
01:14:50.880 because this is where everything should
01:14:52.239 click and you go, "Oh, I now understand
01:14:54.719 how everything works together." And as a
01:14:56.880 quick note, if you haven't watched the
01:14:58.719 beginning of example number five where I
01:15:00.800 break down the core components of
01:15:02.400 sessions, state, and runners, definitely
01:15:04.800 recommend checking that out again before
01:15:06.719 watching this one. But without further
01:15:08.080 ado, let's go ahead and hop over to the
01:15:09.520 code. So now it's time to look at the
01:15:11.600 code for how we can start to save our
01:15:14.320 sessions to a database. So when we close
01:15:16.239 out of an application and restart it, we
01:15:18.560 can still access all of our previous
01:15:20.320 messages. Okay, so let's walk through
01:15:22.080 the five different highle parts of this
01:15:24.400 code so that we can be on the same page.
01:15:26.159 So first things first, our whole goal is
01:15:28.239 we want to begin to save sessions to a
01:15:30.880 database. So what we need to do is we
01:15:33.840 need to say hey I would like to save all
01:15:36.960 my sessions to a specific database file.
01:15:39.840 In this case we're saying I would like
01:15:41.280 to save it to a SQLite file which is
01:15:44.159 basically just a SQL database that's
01:15:46.560 just super easy to work with. And I want
01:15:48.560 the file to be called my agent data
01:15:51.040 database. Now you can see over here in
01:15:53.520 our folder structure I already have an
01:15:55.600 existing database. So you can see
01:15:57.199 whenever we run this code in just a
01:15:58.719 little bit, it's going to create a
01:16:01.120 database file just like this inside of
01:16:03.440 example number six. So that's what it's
01:16:05.520 going to do. Now we can say, all right,
01:16:07.520 when it comes to which sessions I would
01:16:09.520 like to use, well, if you remember in
01:16:10.960 the last example, we were using the
01:16:13.280 inmemory session service. Well, this
01:16:15.840 time we're using the database session
01:16:17.840 service. And quick pro tip, you can save
01:16:20.640 these sessions locally, like these
01:16:22.640 database sessions locally, or if you
01:16:24.640 have a database running in the cloud
01:16:27.040 somewhere hosted like on Google Cloud
01:16:28.719 Platform or another database hosting
01:16:30.880 services, you could point it there as
01:16:32.560 well. But for this example, we're just
01:16:34.000 saving everything locally. All right.
01:16:35.920 Next, what we want to do is define some
01:16:37.840 initial state because what we are trying
01:16:39.600 to do in this example is to create a
01:16:42.400 reminder agent who will take in
01:16:44.320 reminders from us, save these reminders
01:16:46.800 to a list and then when we are done with
01:16:48.960 those reminders, it should remove the
01:16:51.120 reminders from our list. That's exactly
01:16:52.640 what we're trying to build inside this
01:16:54.080 agentic workflow. So, we need to update
01:16:56.320 our initial state to say our name and
01:16:58.560 start off with a blank empty list of
01:17:00.480 reminders. From there, what we're trying
01:17:02.480 to do is begin the process of working
01:17:06.800 with existing sessions and creating new
01:17:08.880 ones. So, imagine if we start creating a
01:17:11.600 new conversation with our agents and
01:17:13.600 it's the first time we're working with
01:17:15.120 them, it should create a new session. If
01:17:17.520 it is the, you know, we've been talking
01:17:19.360 to this agent over and over and over, we
01:17:21.199 should pull out our existing session.
01:17:22.880 So, let me show you how we're doing
01:17:24.239 this. Well, first things first, we need
01:17:26.080 to give our app an application and pass
01:17:29.199 in a user ID. So, we need to have these.
01:17:31.440 And then with inside of our session
01:17:33.280 service, which is going to be our
01:17:34.960 database session service that stored all
01:17:37.120 of our previous conversations in this
01:17:39.280 file, we're going to run the command
01:17:41.199 list sessions. And what this will do is
01:17:44.000 it will look up for this specific
01:17:45.920 application and this specific user. It
01:17:48.320 will look up all existing sessions that
01:17:50.480 we've already had with this agent. From
01:17:52.960 there, we're going to do a quick check.
01:17:55.120 So in option number one, we're going to
01:17:57.199 say, hey, did this existing session
01:17:59.760 already exist? And does it have a length
01:18:02.080 over zero? Meaning like there's there is
01:18:04.480 a session because obviously if there if
01:18:06.400 it exists, the number will be one and
01:18:08.560 greater than zero. And if that's the
01:18:10.239 case, what we're going to do is pull out
01:18:12.159 the session ID from that existing
01:18:14.719 session. So that's how we're going to
01:18:15.920 get our session ID. If this is the first
01:18:18.480 time we've began to chat with this
01:18:20.719 session, what we want to do instead of
01:18:22.960 using the existing one is we want to
01:18:25.120 create a new session. And if that's the
01:18:27.440 case, what we want to do is pass in the
01:18:29.040 app name, the user ID, and initial
01:18:31.280 state. So either way, we're going to be
01:18:33.280 in a great situation where we have a
01:18:35.520 session ID that we can begin to
01:18:37.520 communicate with. Great. So now that we
01:18:39.679 have that session ID, what we can do is
01:18:42.080 begin to start to set up our runner just
01:18:44.560 like we did in example number five. And
01:18:46.239 if you remember the core ingredients of
01:18:47.679 a runner was our agent who's going to be
01:18:50.159 responsible for handling all the
01:18:52.000 requests and has all the instructions
01:18:53.360 and tools and agents everything inside
01:18:54.880 of it. So we want to pass in the root
01:18:56.640 agent and we also need to pass in the
01:18:59.360 specific session service that we've been
01:19:01.760 working with. So in our case remember
01:19:03.360 the session service is nothing more than
01:19:05.679 the initial database session service
01:19:07.760 that we set up from the get- go. Okay
01:19:10.239 great. So now that we have our runner
01:19:12.159 set up, we are set up to start a
01:19:14.719 interactive conversation loop. And this
01:19:17.040 is where we are going to go through the
01:19:19.120 following where we are going to work
01:19:20.719 with a memory agent chat that will
01:19:22.719 remember reminders for us. And whenever
01:19:24.719 we're done chatting with it, we can type
01:19:26.480 in exit or quit and it will kill the
01:19:28.320 conversation for us. So what I would
01:19:30.000 like to do is do a quick run through of
01:19:32.560 this and actually run the agent so you
01:19:35.120 can see in action. And two things I want
01:19:37.360 to do before running it is I want to go
01:19:39.199 clean things up. So, I want to delete
01:19:41.840 our database so that we're running from
01:19:44.000 a clean slate. So, we're deleting the
01:19:46.080 database. And then I want to show you
01:19:48.080 how we're handling each request. So,
01:19:50.400 each user input that we get when we're
01:19:52.239 chatting with it, I want to show you how
01:19:53.760 we handle it. And that's all inside of
01:19:55.600 the call agent async function. I put
01:19:57.840 this in a separate file called
01:19:59.960 utils.py. So, you'll notice in the
01:20:02.080 example 6 folder, I have a utils.py file
01:20:05.120 for you. And this has a few different
01:20:07.440 functions to help make your life
01:20:08.960 simpler. And we as good programmers want
01:20:11.679 to keep our code clean in our main file.
01:20:14.000 So let's walk through this really
01:20:15.280 quickly so you can understand what's
01:20:16.400 going on. So first things first, we're
01:20:18.000 passing in a few different pieces of
01:20:20.000 information. We're passing in the runner
01:20:22.320 that has access to our sessions and it
01:20:25.040 has access to our agent. From there, we
01:20:27.600 want to pass in the user ID. So who's
01:20:29.760 making the request in which session are
01:20:31.920 we working with? And then finally, we
01:20:33.679 want to pass in the raw query, which is
01:20:35.440 like, oh, what did Brandon ask? From
01:20:37.520 there, we need to convert the query we
01:20:40.159 get into a piece of content. And if you
01:20:42.239 remember from example five, a content is
01:20:44.400 nothing more than just a message we want
01:20:46.080 to send over to our agent. From there,
01:20:48.960 what we're going to do is log it. And I
01:20:52.719 have set up a bunch of print statements
01:20:54.640 to make our lives a lot easier so we can
01:20:56.640 inspect what's going on. You'll see this
01:20:58.239 in just a second when we run it. But the
01:20:59.920 core thing that you'll notice is once
01:21:01.600 again we are going to for that runner
01:21:03.840 we're going to call run. Last time we
01:21:05.440 did runner.run and this time we're going
01:21:07.120 to do runner.async. Google ADK
01:21:09.520 recommends to always use runner async
01:21:12.800 and to only use
01:21:14.440 runner.run when you're testing locally.
01:21:16.640 So if you're doing any real world
01:21:18.239 application always use run async. Now
01:21:20.640 once we have that set up for our runner
01:21:22.560 we pass in all the information that
01:21:24.080 we've been working with. So who's making
01:21:25.840 the call? What are the previous messages
01:21:28.159 that we have been using and talking
01:21:30.480 about with this specific user and
01:21:32.400 between them and the agent? And then
01:21:33.679 finally, what is the new message that
01:21:35.440 you want me to work on? From there, the
01:21:37.360 runner is going to go through that life
01:21:38.960 cycle that we talked about last time and
01:21:41.120 we are going to process the agent
01:21:43.600 response. So, let me show you what that
01:21:44.880 looks like. And basically, what we're
01:21:46.960 going to do is iterate through all the
01:21:48.800 different pieces of content that we get.
01:21:51.679 And what the main thing that you want to
01:21:53.920 care about is we're going to log the
01:21:56.400 final response. So if it is the final
01:21:58.480 response, we're going to log it. And so
01:22:01.280 you can see, oh yeah, this is what the
01:22:02.560 agent said. Don't worry, it doesn't
01:22:04.480 matter. A lot of this complex code is
01:22:06.480 all around just printing statements. So
01:22:08.239 you don't really need to to worry about
01:22:09.760 a lot of it. Okay, great. So once we
01:22:12.480 process the agent response and we have
01:22:14.080 it, we log the final response text right
01:22:16.960 here. So we just return the final
01:22:18.320 response. So that's it in a nutshell. I
01:22:20.320 know that was a little bit more
01:22:21.199 complicated, but don't worry. I'm going
01:22:22.400 to run it and it will all make sense.
01:22:24.560 So, let's clear everything out and run
01:22:27.120 the agent so you can see it all in
01:22:28.800 action. And we're going to do two
01:22:30.320 different runs. The first run, we're
01:22:32.080 going to start out with a blank database
01:22:33.840 where it doesn't exist. So, we're going
01:22:35.760 to have ADK create the database file for
01:22:38.239 us. Then, we're going to ask a question
01:22:39.920 or two, create a reminders, and then
01:22:41.520 we're going to close out of the
01:22:42.560 application and restart it so you can
01:22:44.320 see everything in action. So, let's
01:22:46.000 start the fun. So, we are going to
01:22:47.840 inside of file 6 with our virtual
01:22:50.320 environment activated, we are going to
01:22:51.840 run python main.py. And this will allow
01:22:55.199 us to uh it'll spin everything up. In
01:22:57.840 just a second, we should see it created
01:22:59.360 a database file for us. From there, we
01:23:02.320 can now start to add reminders. And I'm
01:23:04.639 going to make this really big so you can
01:23:07.199 see what's going on. So, we're going to
01:23:09.440 say, "Hey, please set a reminder for me
01:23:14.080 to take out the trash tomorrow at 5:00
01:23:19.120 p.m." From there, the agent is going to
01:23:22.320 take in that request. And from there,
01:23:25.040 the agent is going to respond, "I've
01:23:26.639 added your reminder to take out the
01:23:27.920 trash tomorrow at 5:00 p.m." And yeah,
01:23:30.480 so that's what it's saying. And now, as
01:23:32.560 an extra bonus for you guys, I log the
01:23:35.600 state before and after every request.
01:23:38.239 So, you can see the state before
01:23:40.000 processing this message was none. We had
01:23:42.400 zero reminders, but afterwards, the
01:23:45.120 agent created a new reminder for us.
01:23:48.320 Now, how the heck did it do this? How
01:23:50.080 did this agent save a reminder? Well, we
01:23:53.440 didn't fully show this off initially,
01:23:55.600 but if you go to your agent.py pi file.
01:23:57.920 You can see we created I'm going to
01:23:59.920 minimize these so you can see in action.
01:24:02.080 One second. So what you can see is we
01:24:04.880 now have a new memory agent. This memory
01:24:08.320 agent takes in a few core pieces of
01:24:11.040 information. It has a description and it
01:24:13.360 has instructions. And when it comes to
01:24:15.040 instructions, we say, "Hey, you're a
01:24:16.560 friendly reminder assistant. You are
01:24:18.400 working with this shared state
01:24:19.760 information. Specifically, you have
01:24:21.679 access to the person's username and a
01:24:23.600 list of reminders. From there, what I
01:24:25.520 want you to do is you have the following
01:24:27.760 capabilities. You can add new reminders,
01:24:29.840 view existing, update them, delete them,
01:24:31.840 or update the user's username. From
01:24:33.679 there, I give it some extra specific
01:24:35.520 instructions telling it how it should
01:24:37.280 handle the process. The basic CRUD,
01:24:39.600 which stands for create, read, update,
01:24:41.120 and delete. I walk it through the basic
01:24:43.120 operations for creating and working with
01:24:45.840 updating our our different reminders.
01:24:48.320 Now, how do we actually update state and
01:24:51.120 our reminders? Well, the way we do that
01:24:53.600 is through our tools. So, we have added
01:24:56.719 multiple tools to this agent. So,
01:24:59.040 everything from adding, viewing,
01:25:01.040 updating, deleting, and the basic CRUD
01:25:03.520 operations. So, that's why we have all
01:25:05.440 these tools up here. Now, later on when
01:25:07.920 we get to tool context management, we'll
01:25:10.239 work on this more. But the main thing I
01:25:12.239 want you to know is when you are working
01:25:14.480 with state inside of your tool calls,
01:25:16.560 which we'll touch on a lot more when we
01:25:18.560 get to callbacks, what you'll notice is
01:25:20.480 there is this new tool context parameter
01:25:23.120 that we give to tools. Now, what the
01:25:24.960 heck does this mean? Well, basically
01:25:26.480 what's going on is you can pass in
01:25:28.239 whatever parameters you want that you
01:25:29.920 would normally give to a tool and then
01:25:31.840 at the very very end you can pass in
01:25:33.760 tool context and tool context will have
01:25:36.560 access to all sorts of different
01:25:38.560 attributes and specifically it's going
01:25:40.800 to have access to the state. So it has
01:25:43.600 access to all sorts of information. So
01:25:46.000 what we're doing is we're going hey tool
01:25:48.480 context I would like you to give me
01:25:51.440 access to the current state object and I
01:25:53.840 would like you to get all the current
01:25:55.280 reminders. Once I have access to the
01:25:57.280 reminders I would like you to add a new
01:25:59.840 reminder to the list. Once I have that
01:26:01.840 new reminder I want to save it back to
01:26:04.239 state. So this is how you add
01:26:06.320 information to state. You just call
01:26:08.480 state have the key and then pass in the
01:26:10.719 new value. And then from there, what
01:26:12.239 we're doing with our tool call, cuz
01:26:13.920 earlier in our example number two, when
01:26:15.840 we learned about tools, you learned that
01:26:18.080 you want to make sure your tool return
01:26:20.000 statements are as informative as
01:26:21.840 possible. So in our case, we're
01:26:23.840 returning the fact the action. We're
01:26:26.000 passing back the reminder, and we're
01:26:28.000 passing back a message saying, "Hey, I
01:26:29.679 successfully added this reminder." And
01:26:31.679 this is the exact same flow we follow
01:26:33.840 for all of our different tool calls. So
01:26:35.679 when it comes to viewing our reminders,
01:26:37.840 all we need to do is inside a tool
01:26:40.239 context, we just need to access the tool
01:26:43.920 state. We want to get reminders and then
01:26:46.080 return them. And it's the exact same
01:26:48.000 thing for all the rest of the different
01:26:49.920 tools. We just pass in some variables,
01:26:52.320 pass in the tool context, pull out what
01:26:54.320 we need, and then save it back to state.
01:26:56.239 So that's exactly what's going on. So
01:26:58.400 we've kind of gone a little bit in the
01:26:59.600 weeds, but what I want to do is add in
01:27:01.920 one more reminder. Then we're going to
01:27:03.760 close out of the application, rerun it.
01:27:05.760 So you can see that yes, it is properly
01:27:07.600 saving things to our database. So let's
01:27:09.520 also say also remind me to mow the grass
01:27:15.040 this weekend. From there, it's going to
01:27:17.920 update and add a new reminder using
01:27:20.000 those tools that you just saw. So life's
01:27:22.320 good. So what we're going to do now is
01:27:24.800 we are going to kill the application. So
01:27:26.480 you can do that just by typing quit.
01:27:28.080 This will end the conversation. Life's
01:27:30.000 good. Your data has already been saved
01:27:31.760 to the database. We didn't have to do
01:27:33.520 anything extra. ADK new by providing
01:27:36.480 that initial sorry let me minimize this
01:27:38.960 for you guys. ADK new by providing in
01:27:42.080 that initial database service it would
01:27:44.159 automatically save everything to the
01:27:45.679 database. So let's have some fun and see
01:27:48.000 what was saved to our database. So when
01:27:49.760 you click in the database if you're
01:27:51.520 using cursor you should be able to see a
01:27:53.199 database viewer just like this. And what
01:27:55.360 you can see is it saved all sorts of
01:27:57.760 information to session. It saved app
01:28:00.239 state, raw events, sessions, and user
01:28:03.120 state. So if I open up sessions and
01:28:06.320 double click on it, you can see that we
01:28:08.800 have a session state between the user AI
01:28:11.280 with Brandon. We have a session ID and
01:28:13.840 you can see the state of where we left
01:28:16.080 off. And if you look in the state right
01:28:18.400 now, you can see it includes everything
01:28:20.320 that we just added a second ago. So my
01:28:22.639 username and the list of reminders,
01:28:24.639 which are take out the trash and mow the
01:28:26.320 grass. So you can see it's all being
01:28:27.920 saved to a database now. And if you want
01:28:30.080 as well, you can click inside of events
01:28:32.400 and you can see all of the raw events
01:28:35.120 that happened inside of your
01:28:36.400 application. As you get larger
01:28:38.400 applications, it wouldn't just show for
01:28:40.560 a specific user, it would show for all
01:28:42.320 users. So this is a really nice way to
01:28:44.000 see what's happening inside of your
01:28:45.600 agentic workflows. And like we talked
01:28:47.600 about earlier, there are two different
01:28:49.360 types of messages. And in this case,
01:28:52.239 there are, you know, agent messages and
01:28:54.400 then user messages. If we and we should
01:28:56.800 also probably start to see some tool
01:28:58.239 calls. Yep. Just like this. So you can
01:29:00.560 see some messages like a user request
01:29:02.880 from me which is hey please do this. You
01:29:05.600 can see that it involves a function call
01:29:08.000 which is hey please go save. If we just
01:29:10.320 click in it you can see it's calling
01:29:12.960 doing a function call to the add
01:29:16.000 reminder function and from there it's
01:29:18.159 passing in the raw text of what the tool
01:29:20.560 needs to do. From there you can see the
01:29:23.760 function response included the exact
01:29:26.400 response that we wanted. So the function
01:29:28.239 response now includes that message we
01:29:31.040 said that was very verbose which
01:29:33.360 included the raw action. It included the
01:29:35.920 renew reminder and a message about the
01:29:38.080 action that just occurred. So you can
01:29:39.520 see this is all getting saved to a
01:29:41.280 database. All around absolutely love it.
01:29:43.600 So what we're going to do next is let's
01:29:45.440 close out of our database. We're going
01:29:47.360 to clear things out and rerun the same
01:29:49.760 command. So now when we begin to talk
01:29:52.639 with our memory agent again I can say
01:29:55.040 hey what are my current reminders. From
01:29:59.760 there it's going to access our state per
01:30:02.800 usual and it's going to say all right
01:30:04.880 Brandon here are your current reminders.
01:30:06.880 And at this point it's showing the
01:30:08.560 reminders we already had saved to our
01:30:10.560 session and which our session was saved
01:30:12.560 to a database. So all around, I hope you
01:30:14.880 guys are like freaking out and saying
01:30:16.480 like, "Oh my gosh, I now understand how
01:30:18.400 everything works when it comes to
01:30:20.000 session. I understand what runners do. I
01:30:21.920 understand how sessions can be saved to
01:30:23.520 memory or to a database and kind of see
01:30:25.600 how it all clicks together." I know we
01:30:27.280 did talk on a few additional topics like
01:30:29.920 I didn't really mean to talk about tool
01:30:31.360 context, but hopefully it was helpful to
01:30:32.880 see how tools can access state so you
01:30:35.040 could see how we were altering the state
01:30:37.360 as we were starting to make tool calls
01:30:38.880 with our agents. So, I know that was a
01:30:40.320 little bit of a side quest, but
01:30:41.440 hopefully it was super helpful to see.
01:30:43.360 And don't worry, as we begin to work
01:30:45.199 with callbacks, you're going to see a
01:30:46.880 lot more on that. Okay, great. Well,
01:30:48.480 give yourself a pat on the back. We are
01:30:50.000 halfway done with you mastering ADK. And
01:30:52.800 now we're going to move on to our next
01:30:54.320 example. So, I'll see you guys in the
01:30:55.920 next one. Hey guys, and welcome to
01:30:57.440 example number seven where we're going
01:30:59.120 to look at our first multi- aent system.
01:31:01.840 So excited for this one. And what we're
01:31:04.239 going to do is break this up into three
01:31:05.760 different parts. First, we're going to
01:31:07.360 head over to the whiteboard so you can
01:31:08.719 understand how multi- aent systems work
01:31:11.440 inside of ADK because it's completely
01:31:13.679 different from what you would expect to
01:31:15.120 see in Crew AI or Langchain. From there,
01:31:17.360 once we understand how things work,
01:31:19.280 we're going to look at a simple code
01:31:20.880 example of our first multi- aent system.
01:31:23.360 And then finally, in part three, we're
01:31:24.719 going to run it so you can see
01:31:25.679 everything in action. So, let's go ahead
01:31:26.960 and head over to the whiteboard so we
01:31:28.719 can break down some of the core patterns
01:31:30.400 and behaviors of multi- aent and ADK.
01:31:32.960 All right, so let's start investigating
01:31:35.280 how the heck do multi- aent systems work
01:31:38.320 inside of ADK. Now, what I want to do in
01:31:40.719 this first example is give you a brief
01:31:42.719 overview of an example agent. So, let's
01:31:46.320 imagine we have a root agent because you
01:31:48.880 always have to have a root agent inside
01:31:51.440 of your ADK setups. This root agent is
01:31:54.480 usually considered the delegator or the
01:31:57.040 manager or usually this agent is
01:31:59.280 responsible for delegating work to other
01:32:01.679 agents. That's usually the entry point
01:32:03.520 to everything inside of your
01:32:04.560 application. Now, here is where ADK is
01:32:07.360 different than other frameworks compared
01:32:09.679 to like Crew AI and link chain. What
01:32:12.000 happens inside of ADK is whenever you
01:32:15.520 send a request into the framework and
01:32:19.120 specifically to your agent, what this
01:32:20.880 agent is looking to do is answer the
01:32:23.120 query as quickly as possible. So, let me
01:32:25.199 give you an example and then walk you
01:32:26.480 through why it's different than other
01:32:28.000 solutions. So if you pass in a query
01:32:31.280 such as, hey, what is the weather today?
01:32:33.679 This agent is going to look at the
01:32:36.040 description of all of its sub agents and
01:32:39.520 figure out which one is the best suited
01:32:42.960 to answer the query. Once it knows who
01:32:45.520 to pass the work to, the root agent is
01:32:47.920 out of the picture. It delegates all the
01:32:50.360 responsibilities to this sub agent who
01:32:52.719 takes control and handles it from there.
01:32:55.040 From there, this weather agent then
01:32:57.679 determines based on the query, well, it
01:32:59.760 determines, well, what tool calls should
01:33:02.080 I make in order to answer the question.
01:33:04.800 So then it goes, oh, it looks like you
01:33:06.480 want to know the weather today. Well, I
01:33:08.000 will look up the weather in Atlanta,
01:33:10.080 Georgia. From there, once it gets the
01:33:11.840 answer, the weather agent will then
01:33:13.679 know, okay, I know the results from the
01:33:15.360 tool call. I can now generate a result
01:33:17.600 and the weather agent will return the
01:33:19.360 final response. Now this is totally
01:33:21.600 different than other frameworks like
01:33:23.440 Crew AI because in Crew AI what normally
01:33:26.239 happens is you have one task and then
01:33:29.120 for that task you usually have multiple
01:33:31.760 agents trying to work on it. So in crew
01:33:34.080 AI you would expect to see something
01:33:35.600 like this where you have get weather and
01:33:39.280 what you would expect to see is you
01:33:41.280 would have multiple agents working on
01:33:42.960 it. So you'd have a weather agent, you
01:33:44.960 would have a research agent, and then
01:33:47.600 you would have someone else and together
01:33:50.560 these agents would work together to
01:33:53.120 answer the question and collaborate to
01:33:56.239 answer it. That is not the case in ADK.
01:33:58.800 It is all about delegation and single
01:34:01.199 answers. There is no at least not yet.
01:34:04.480 We haven't worked on workflows, but at
01:34:06.400 at a basic example of working with
01:34:08.320 agents, it is all about delegating and
01:34:10.400 immediately answering the question. This
01:34:12.080 was something that confused me a ton
01:34:13.440 when I started out with ADK and I just
01:34:16.000 wanted to make sure you guys understand
01:34:17.600 this core principle. So key takeaways,
01:34:20.000 we focus on delegation inside ADK and
01:34:23.280 whoever is the best suited to answer the
01:34:25.120 question, they get to work on it and
01:34:26.800 they get to generate the result. There's
01:34:28.800 no multi-iterating over and over and
01:34:31.199 over at the basic examples of ADK. We'll
01:34:33.920 get to workflows later on, but just know
01:34:35.120 at a basic level there's no no looping
01:34:37.440 multiple attempts. Whenever you set up
01:34:39.280 your basic multi-agent systems, they
01:34:41.120 just answer the question as quickly as
01:34:42.480 they can to get you an answer. Okay,
01:34:44.639 cool. Now, we need to look at some of
01:34:46.960 the core limitations of working with
01:34:48.800 ADK. So, whenever you create agents,
01:34:52.000 sometimes you want to use all the cool
01:34:54.400 new built-in tools that ADK creates for
01:34:57.040 you. However, when you look at the
01:34:59.440 documentation for working with these
01:35:01.360 agents, it specifically says that, hey,
01:35:04.080 you cannot use built-in tools within a
01:35:06.639 sub agent. This tripped me up because I
01:35:08.639 was like, why doesn't this work? Why
01:35:09.920 doesn't this work? Well, don't worry. It
01:35:11.920 is because you cannot use built-in tools
01:35:14.159 with sub agents. So, for example, this
01:35:16.639 would break if you had a root agent who
01:35:19.760 was just a general researcher agent who
01:35:22.080 was responsible for delegating out to uh
01:35:24.320 sorry, it was a manager agent who's
01:35:26.159 responsible for delegating out work. If
01:35:28.159 you had a random request of like, hey,
01:35:30.159 what's going on in the news today? Well,
01:35:32.800 this would fall under the search agent
01:35:34.800 and this search agent would try to call
01:35:36.560 the built-in Google search tool. This
01:35:38.880 would break. You're going to get a huge
01:35:40.239 error saying you can't do this and it's
01:35:41.840 not the most clear error and you it's up
01:35:44.080 to you to know that this limitation
01:35:46.159 exists. Now, there is a workaround to
01:35:48.960 get this to work and let me steal the
01:35:50.960 ball over here and walk you through it.
01:35:53.120 So, there is a workaround. If you did
01:35:55.040 want to look up a generic search request
01:35:56.960 of like, hey, what is going on in the
01:35:59.120 news today? What you can do is use the
01:36:02.880 command agent as tool. And what this
01:36:05.600 will do is it will treat your agents as
01:36:07.679 a tool call. So this is the only way to
01:36:10.400 work around it to use if you wanted to
01:36:12.320 use tools like Google search in a sub
01:36:14.639 agent, you have to use this agent as
01:36:16.719 tool. Don't worry, you're going to see
01:36:17.679 this in the code in just just a second.
01:36:20.000 But just know whenever you do this
01:36:21.360 setup, what happens is the root agent
01:36:23.440 goes, "Oh, okay. Well, what I'll do
01:36:26.320 because I want to look up the weather is
01:36:28.320 I will or look up what's happening in
01:36:30.159 the news. I will call this pathway like
01:36:34.000 a normal tool where I pass in parameters
01:36:36.080 and everything else to get an answer and
01:36:38.159 then this will work. But this is just a
01:36:40.239 weird workaround. If you want to use any
01:36:41.679 built-in tools like Google search, if
01:36:43.679 you want to use the vector search AI or
01:36:45.520 the code execution tool built in from
01:36:47.600 Google, this is the path you have to do.
01:36:49.600 Now, I did mention a while ago that hey,
01:36:52.320 there are a few different workarounds.
01:36:54.320 So if you don't want the behavior of the
01:36:56.960 agents, you know, just doing a single
01:36:58.719 shot where they're delegating the work
01:37:00.480 to let the other agents handle all the
01:37:02.320 requests, what you can do is work with
01:37:05.119 these different types of workflow agents
01:37:07.199 that we're going to cover in examples
01:37:09.119 10, 11, and 12 where we focus on
01:37:11.679 parallel. I got to spell correctly for
01:37:13.760 this to work. Parallel agents,
01:37:15.520 sequential agents, and loop agents. This
01:37:17.280 is where we can start to have agents
01:37:18.800 take multiple attempts at solving
01:37:20.719 answer. And don't worry, we're going to
01:37:21.760 look at these at the very end. So, I
01:37:23.600 just want to clear up a few different
01:37:24.719 things because multi- aent systems in
01:37:26.880 ADK are different than anything else
01:37:28.480 you've ever seen. But I want to go ahead
01:37:30.239 and walk you through the core lessons
01:37:32.320 which were everything gets delegated.
01:37:34.480 You cannot use built-in tools and sub
01:37:36.719 aents. If you do want to, you need to
01:37:39.280 use the agent as tool wrapper. All
01:37:41.760 right, now you've seen all the highlevel
01:37:43.760 lessons. Let's dive into the code so you
01:37:45.840 can see everything in action. See you in
01:37:47.280 just a second. Okay, so now it's time
01:37:49.119 for us to look at the code for our first
01:37:51.760 multi- aent system. We're getting
01:37:54.000 advanced, guys. We've gone from a single
01:37:55.760 to multiple. So, here is a brief
01:37:58.560 overview before we dive in of everything
01:38:00.639 that's going on. So, first things first,
01:38:02.880 we are creating a new agent just like we
01:38:04.800 have this whole time. The name needs to
01:38:06.800 match our folder name because we are
01:38:08.560 right now in example number seven. From
01:38:10.400 there, we're going to give it a model
01:38:11.600 just like we normally do. And then we
01:38:14.159 are going to give our agent
01:38:15.920 instructions. So we're going to say hey
01:38:18.239 you are a manager agent just to be very
01:38:20.800 clear that your job is to delegate and
01:38:23.920 you always want to delegate the task to
01:38:25.920 the appropriate agent. Here are the
01:38:28.159 different basically task you are allowed
01:38:30.000 to delegate to other agents. So we're
01:38:32.400 saying you have two agents. The stock
01:38:34.800 analysis agent and then a funny nerd
01:38:37.280 agent who tells this joke. And then to
01:38:38.960 help give you guys some additional
01:38:40.560 examples we're also providing this
01:38:42.480 manager agent some tools. So, if these
01:38:45.280 agents can't handle it, we're going to
01:38:47.360 pass it along to these tools. Now, here
01:38:50.000 are the big changes that you're going to
01:38:52.400 notice inside of multi-agent solutions.
01:38:55.040 So, the first one is we now have a sub
01:38:57.280 agent property, which is a list, and we
01:39:00.239 can pass in additional agents in here.
01:39:03.520 And as you remember from the whiteboard
01:39:05.440 session, anytime we answer a question,
01:39:08.000 if one of these agents is fit best to do
01:39:10.960 the task, we pass the task over to these
01:39:13.600 agents and they handle managing the
01:39:15.600 response and doing all the work. Now,
01:39:17.679 how do we actually get these agents
01:39:19.280 inside of our main root agent? Well,
01:39:21.840 super easy. What we do is we import
01:39:24.239 these agents from our sub agent folder.
01:39:27.679 So, inside our sub aent folder, this is
01:39:30.000 where we have pretty much everything
01:39:31.360 that you would expect to see. We have
01:39:33.360 our funny nerd and we have our stock
01:39:35.600 analyst and we have our news analyst.
01:39:37.920 More on the news analyst in a second
01:39:39.840 when we start to talk about agent tools.
01:39:41.760 But what you'll notice is inside of each
01:39:43.600 of these sub agents, it's the exact same
01:39:46.320 folder structure that you've seen for
01:39:47.840 everything so far where you have a
01:39:49.600 folder. In the folder, you have an
01:39:51.119 agent. That agent needs to have a name
01:39:54.560 that matches the name here. So, rinse
01:39:56.800 and repeat. Same thing you guys have
01:39:58.239 been doing this whole time. Now, what we
01:40:00.239 can do is look at how do you import
01:40:02.560 these? Well, up top in the root of your
01:40:05.199 root agent folder, you'll just import
01:40:07.440 from the sub agent folder, call out the
01:40:10.320 package right here. So, this is the
01:40:11.679 funny nerd package and we want to grab
01:40:13.920 the agent folder. Once we grab the the
01:40:16.080 agent file, sorry, what we want to do is
01:40:18.320 inside the agent file, we want to import
01:40:20.960 the funny nerd agent. So, that's exactly
01:40:23.280 why these imports look just like they
01:40:25.760 do. Okay. Now, what we're going to do,
01:40:28.080 just so we're on the same page, I'm
01:40:29.679 going to give you a brief overview of
01:40:31.440 each one of these agents and then we're
01:40:33.440 going to dive into the tools so you can
01:40:35.520 see how this agent as tool functionality
01:40:38.159 works as well. So, let's first go look
01:40:39.679 at our stock agent. Super
01:40:41.360 straightforward agent. The important
01:40:43.280 thing to note here is when it comes to
01:40:45.920 multi- aent systems, in order for the
01:40:48.560 root agent to know what each of its sub
01:40:51.360 agents can do is it looks at the
01:40:53.600 description. This description decides
01:40:56.159 and tells the parent agent, hey, here's
01:40:58.400 what I can do and here's how I can help.
01:41:00.080 So, if anyone asks a question around
01:41:02.480 looking up stock prices or looking at
01:41:04.239 them over time, I can do that. That is
01:41:06.080 my core functionality and I can help
01:41:07.600 with it. And then this agent is has a
01:41:10.639 singular function where all it does is
01:41:12.880 it gets a stock price for a current
01:41:14.560 ticker. So, it just gets the yeah gets
01:41:16.239 current stock price. The other agent
01:41:18.400 that we have is our funny nerd. our
01:41:20.639 funny nerd. Once again, same model, same
01:41:23.199 name as the parent. And what it does is
01:41:26.159 it says this agent tells funny nerdy
01:41:29.040 jokes. So anytime we want a joke, this
01:41:30.960 model will get picked. And from there,
01:41:33.280 the final thing that we're going to do
01:41:34.880 is now that you've seen these agents in
01:41:36.880 action, let's quickly look at our news
01:41:39.600 agent because this agent does it breaks
01:41:42.880 one of our rules because this agent
01:41:45.199 imports one of the built-in tools from
01:41:47.600 ADK. And because this agent imports
01:41:50.960 Google search, we can no longer call
01:41:54.080 this agent as a sub agent. For example,
01:41:56.080 if we did this, this would break. I'll
01:41:58.320 show it to you that it does break in a
01:41:59.600 little bit in case you do run into the
01:42:00.719 same error. But the important thing is
01:42:02.480 we have to wrap it as agent tool. Now,
01:42:04.560 why do we have to do this and what's the
01:42:06.080 difference when we do this? Well, if you
01:42:07.760 head over to the core docs inside of
01:42:10.400 what agent development has and you look
01:42:12.639 at the key differences of working with
01:42:14.639 sub aents, here's what's happening.
01:42:16.639 Whenever you do agent as a tool,
01:42:18.480 whenever the parent agent calls the
01:42:21.119 child agent as a tool, basically what
01:42:23.280 happens is the result from agent of the
01:42:25.920 child agent gets passed back to the
01:42:28.960 parent agent and then the parent agent
01:42:30.960 uses that answer to generate a response.
01:42:34.000 So basically the child gets called. This
01:42:36.400 child agent which is agent A in this
01:42:38.320 case does all the work calls all its
01:42:40.239 tools in our case the built-in tool and
01:42:42.239 then it returns the answer back to the
01:42:43.920 parent and then the parent uses that to
01:42:45.600 respond. Whereas with sub agents, it
01:42:47.679 does exactly like we said earlier, which
01:42:49.440 is when a parent agent delegates to a
01:42:51.760 sub agent, the responsibility of
01:42:53.360 answering is completely transferred to
01:42:55.520 the child agent where agent A is out of
01:42:57.760 the loop going forward. So that is going
01:43:00.000 back to the key principle earlier of
01:43:01.520 everything gets delegated in multi- aent
01:43:03.679 systems. All right. So, now that you've
01:43:05.679 kind of seen this in action, what is
01:43:07.760 this news analyst or or sorry, you
01:43:09.679 already saw the news analyst and the way
01:43:11.040 we use this news analyst to not break is
01:43:13.679 we wrap it inside of agent tool and you
01:43:16.639 can import agent tool just like this.
01:43:19.440 So, this is how you do it. Google ADK
01:43:21.360 tools agent tool and we want to put
01:43:23.119 agent tool and that's how you wrap your
01:43:24.719 agents to make them tools. Pretty
01:43:26.239 straightforward. Okay. So, now that
01:43:28.080 you've seen this at a high level, what I
01:43:29.760 would like to do is start to run the
01:43:32.320 code. and you're going to see how it
01:43:34.480 works at a high level. We're going to
01:43:35.840 look at events state, how it all gets
01:43:37.840 updated. And then finally, what we're
01:43:39.600 going to do afterwards is I'm going to
01:43:40.880 break the program where I'm going to not
01:43:43.280 wrap this inside agent tool just so you
01:43:45.440 can see the type of errors you would get
01:43:46.719 in case you ever accidentally make this
01:43:48.000 mistake yourself. So, what are we going
01:43:49.520 to do? We are going to make sure we
01:43:52.080 first off are in the right folder,
01:43:54.400 multi- aent, and we've activated our
01:43:56.480 virtual environment. Now, we're going to
01:43:57.760 run it. Once we run it, it's going to
01:44:00.080 spin up our web interface that we've
01:44:01.840 seen a thousand times that looks just
01:44:04.000 like this. And now what we can do is
01:44:06.159 start to interface with our agents. So
01:44:08.080 up in the top, let's actually make this
01:44:09.600 a little bit bigger for you guys. So
01:44:12.320 even a little bit bigger. Great. So what
01:44:14.480 you'll notice is there's only one agent
01:44:16.080 because our we only have one root agent.
01:44:18.320 So now what we can do is say, please
01:44:21.520 tell me a funny joke. And what we would
01:44:24.960 expect to happen is the root agent would
01:44:27.960 transfer over to the joke agent and the
01:44:31.520 joke agent would then generate the
01:44:33.199 response. So here we can actually look
01:44:35.040 at the series of events that triggered
01:44:37.119 this. So transfer to agent, we can start
01:44:39.520 to see a little bit of an overview.
01:44:41.679 Yeah, it's just starting to get a little
01:44:42.800 bit bigger. So you what you can see is
01:44:44.719 the manager agent goes, okay, I have
01:44:47.760 these different agents and tools at my
01:44:50.480 disposal. Now I've been asked to
01:44:52.800 generate a funny joke. So we are going
01:44:55.440 to now do it make a function call to
01:44:58.159 pass over this query to the funny nerd
01:45:00.880 and we are going to transfer over to
01:45:02.400 this agent. So if we go over to the next
01:45:05.040 event we should start to see that the
01:45:08.159 yeah sorry if we go over to the next
01:45:09.520 event you should start to see that the
01:45:10.800 funny nerd is now responsible for
01:45:13.600 handling this request. And you can see
01:45:15.760 that the funny nerd is like the code
01:45:18.159 told it to do is ask what it would like
01:45:20.320 to to generate a joke around. So if you
01:45:22.719 per usual go and look at the what the
01:45:25.040 code is, it put together the prompt and
01:45:27.520 basically well I'm not going to go too
01:45:28.719 deep into that. That's too beginner for
01:45:30.800 you guys. But the important thing now is
01:45:33.119 you can say all right what would you
01:45:34.480 like a joke about? Would you want to
01:45:35.679 hear about Python, JavaScript, whatever
01:45:37.199 you'd like. So we'll say we'll do a joke
01:45:38.800 on Python. And then now what we should
01:45:40.880 see is we have quite a few more events.
01:45:43.280 So if we start to look at them, you can
01:45:45.119 see now that we've asked to get a
01:45:46.880 specific joke for a specific tool. It's
01:45:49.840 going to call the get nerd joke for the
01:45:52.560 topic Python. And now it's going to
01:45:54.639 return a nerdy joke around Python. So
01:45:57.280 yeah, that's exactly what it did. Okay,
01:45:59.040 cool. Well, what other tools do we have
01:46:01.760 access to? So let's quickly look really
01:46:03.760 quick and see. All right, the other one
01:46:05.440 we could do is stocks. So tell me the
01:46:08.400 current stock price of Microsoft because
01:46:12.239 it shot up
01:46:13.639 today. Now what this is going to go do
01:46:16.520 is oh see so now we are still currently
01:46:19.600 in the funny nerd joke. So what we could
01:46:22.880 do is we would normally want to so now
01:46:25.199 that we've been delegated from the root
01:46:27.119 manager to the funny nerd we are now
01:46:30.400 stuck with the funny nerd. So usually
01:46:32.239 you can sometimes get delegated out of
01:46:34.000 this. So what we can do is mention the
01:46:36.960 word delegate. So
01:46:38.679 delegate gate to the root agent then
01:46:43.360 tell me the current stock price of
01:46:45.320 Microsoft. Sometimes this will work.
01:46:47.360 Yeah. So if you're already in an agent
01:46:49.679 that is like a funny nerd, it doesn't
01:46:51.920 always do the best job of delegating. So
01:46:54.159 sometimes you have to mention, hey, you
01:46:55.760 need to refer me to another agent. Now
01:46:58.159 what we can do is you can now see that
01:46:59.920 we were transferred from the funny nerd
01:47:02.800 back to the manager and once we were in
01:47:05.440 the manager we eventually get
01:47:07.360 transferred over to the stock analyst.
01:47:09.760 So what you can see now is the stock
01:47:11.520 analyst called the proper tool and the
01:47:13.760 tool returned the current price of
01:47:15.840 Microsoft which is as of today $424.
01:47:19.600 This was a weird quirk. This probably
01:47:22.239 has happened to me one out of 10 times.
01:47:24.320 Normally if an agent is over its TED it
01:47:27.119 just automatically does this rerouting
01:47:29.679 for you. So that's probably something
01:47:31.920 that we should have updated the prompt
01:47:33.840 to say like hey if you get a request
01:47:36.239 that you are not comfortable answering
01:47:38.159 delegate back to the parent. So that was
01:47:40.159 just a weak prompting on my part. Now
01:47:42.719 what we can do so you can just see a few
01:47:44.239 other things. Let's just say what is the
01:47:48.119 news for today. And what this should do
01:47:51.679 is yeah, so we need to say delegate
01:47:54.080 again. So yeah, I just should have
01:47:55.760 improved the prompting to say if you
01:47:57.040 can't handle the request, delegate to
01:47:58.560 the manager. Delegate to the manager,
01:48:02.000 then tell me the news. Now, this will,
01:48:05.199 per usual, transfer transfer. And now
01:48:07.199 we're going to go over to the news
01:48:08.400 analyst. The news analyst is going to
01:48:10.080 use the Google search tool to find it
01:48:12.560 and then give me a summary of today.
01:48:14.080 Okay, great. So, you've now seen how we
01:48:16.159 can start to work in multi- aent
01:48:18.480 systems. Now, what I want to do is break
01:48:20.560 things because that is fun. So, let's
01:48:22.880 what we can do is get the news analyst
01:48:25.679 out of here. We're going to move the
01:48:27.440 news analyst here just so you can see
01:48:29.920 what the error would be. So, if we
01:48:31.920 respin up our server, what you'll notice
01:48:34.000 now whenever I go to type into our
01:48:36.960 editor. So, if I do I'll just show you.
01:48:39.440 So, I can say get the current time. So I
01:48:42.320 can show you it still works unless we
01:48:44.159 call the the bad agent. So get the
01:48:46.000 current time. So this will get the
01:48:48.480 current time call the tool. Everything
01:48:50.000 looks great. But if I now say please
01:48:52.800 look up the current news for today, this
01:48:58.080 will break and it'll say, "Oops, this
01:49:00.560 tool is being used with function calling
01:49:03.199 that's unsupported." Which is a bad way
01:49:05.679 of saying, "Hey, you're being silly.
01:49:08.239 you're trying to call a tool that you're
01:49:11.360 not allowed to. So, you're trying to use
01:49:13.119 an agent that is not that is supposed to
01:49:15.360 be wrapped in agent as tool. So, I just
01:49:17.440 wanted to show you guys that because
01:49:19.040 that when that broke the first time for
01:49:20.560 me, I was like, what's going wrong? So,
01:49:21.920 I just wanted you guys to see the error.
01:49:23.760 And then quick other thing I did want to
01:49:25.600 mention so you guys can see what I was
01:49:27.679 talking about earlier. What we should
01:49:29.199 have said over in our other prompts to
01:49:31.280 say like if the user asks about anything
01:49:36.280 else, what you should say is you
01:49:39.480 should
01:49:41.080 delegate get the task to the manager
01:49:44.719 agent. So if we just run it again just
01:49:46.719 to show you guys all this. This is a
01:49:48.480 little bit of live debugging so you get
01:49:49.600 to see behind the scenes a little bit.
01:49:51.440 So what happens now is we'll ask to get
01:49:53.760 a funny joke and then we'll ask to get
01:49:55.280 the news just so you can see that it
01:49:57.119 does delegate properly. So we have to be
01:49:59.600 hyper specific with these agents because
01:50:01.280 they don't they only act on what
01:50:03.199 information we give them. Great. So it's
01:50:04.800 up and running again. So now we can say
01:50:07.199 tell me a funny joke. Now this will go
01:50:11.199 find a funny joke. We've been
01:50:13.280 transferred over to the proper agent now
01:50:16.000 which is going to be yeah the funny
01:50:17.679 agent. Yeah. So now we're talking with
01:50:19.280 the funny nerd. And now we can say
01:50:21.880 actually get me the current news for
01:50:26.840 today. And then now it should delegate
01:50:29.360 us properly over to the proper agent.
01:50:31.760 Great. So now we're getting delegated.
01:50:33.199 We're transferred over to the the funny.
01:50:36.320 Yeah, sorry. It's it's struggling to
01:50:39.360 Yeah, it's ending up in a awkward loop.
01:50:41.600 So we can actually kill it and sometimes
01:50:44.800 Yes. So it's like stuck in a loop right
01:50:46.400 now going back and forth. So yeah. So
01:50:47.840 sometime sometimes it is not the most
01:50:49.440 reliable on delegating. So what we can
01:50:52.239 do because it's it's actually struggling
01:50:54.239 really hard. No joke anymore. Just give
01:50:59.040 me the
01:51:00.520 news for
01:51:02.440 today. Great. So you can see now it's
01:51:05.119 transferring. Yeah. So it was just
01:51:06.719 because it was in a weird state between
01:51:08.000 the two, but now we're properly getting
01:51:09.679 delegated to the news and now it's
01:51:11.280 there. So, long story short, what we
01:51:13.280 could have done is just been more
01:51:15.199 instructive inside of our agent in
01:51:17.840 descriptions and just said, "Hey, only
01:51:19.520 answer questions. If anything ever goes
01:51:21.119 wrong that you can't help, always just
01:51:22.639 delegate back to the root agent." And
01:51:24.080 that would have solved the problem. So,
01:51:25.520 hopefully you guys got to see some of
01:51:27.040 the cool parts of multi- aents. You got
01:51:29.199 to see the limitations of why we have to
01:51:32.080 use agent tool calls. You saw how we
01:51:34.400 could improve our agent descriptions in
01:51:37.520 case anything goes wrong to say delegate
01:51:39.199 to the manager agent to help with
01:51:40.639 delegation processes and you got to see
01:51:42.719 a little bit of debugging along the way.
01:51:44.480 So, what we're going to move on next is
01:51:46.159 we're going to hop over to working with
01:51:48.159 our multi- aent solution, but we're
01:51:49.920 going to now start working with shared
01:51:51.440 state that we are going to share between
01:51:53.199 our agents just so you can see that in
01:51:54.960 action. So, let's hop over to example
01:51:56.960 number eight. And if you have any
01:51:58.239 questions on anything so far, feel free
01:52:00.000 drop a comment down below and I will
01:52:01.360 happily help out. Thanks, guys. Talk to
01:52:02.719 you in the next one. Hey guys, and
01:52:03.920 welcome to example number eight where
01:52:05.679 we're going to focus on building a
01:52:07.119 multi- aent system that starts to
01:52:09.040 interact with state. And so excited for
01:52:11.040 you guys to see this one because this is
01:52:12.400 where we start to add in some additional
01:52:14.320 complexity and really start to allow our
01:52:16.639 agents to solve complex problems. And
01:52:18.719 I'm so pumped for you guys to see this
01:52:20.719 agent workflow in action because we're
01:52:22.800 going to be building a customer service
01:52:24.480 agent that has multiple sub agents that
01:52:27.199 basically allow us to handle all
01:52:29.280 customer support for a course. That's
01:52:31.840 basically the demo that we're going to
01:52:33.280 be focusing on. So, let's break down the
01:52:35.040 three different parts of this example.
01:52:37.119 First things first, we're going to head
01:52:38.400 over to our whiteboard where we're going
01:52:40.480 to break down how all these agents work
01:52:42.400 together in order to handle all parts of
01:52:44.960 customer service for a course that we're
01:52:46.560 selling. From there, after we understand
01:52:48.159 the high level of what's going on, we're
01:52:49.920 going to dive into the code so you can
01:52:51.440 see exactly how everything works
01:52:52.800 together. And then finally, we're going
01:52:54.480 to run this agent so you can see it in
01:52:56.400 action. So, let's hop over to the
01:52:57.599 whiteboard so we understand what's going
01:52:58.960 on and how we're going to build a multi-
01:53:00.960 aent system to handle our course sales.
01:53:02.880 All right, so let's look at the multi-
01:53:05.280 aent system that we're building that's
01:53:07.199 going to help us with all sorts of
01:53:08.880 customer service for a course that we're
01:53:11.040 selling. So, at a high level, what we're
01:53:12.960 doing is we've created a customer
01:53:14.719 service root agent that has four
01:53:17.440 different sub agents in that it can work
01:53:19.840 with. Now, let's do a quick overview of
01:53:21.520 what each one of these agents can do.
01:53:23.440 So, first things first is we have a
01:53:25.520 policy agent that just gives some
01:53:27.520 general information about the policy for
01:53:29.599 the AI developer accelerator course that
01:53:31.760 we're selling and it can answer all
01:53:33.360 sorts of questions, refund questions,
01:53:35.280 anything you know related to just
01:53:37.040 general questions answering that our
01:53:38.800 customers might have. From there,
01:53:40.400 anytime someone wants to purchase a
01:53:42.159 course, they're going to be directed to
01:53:43.920 our sales agent. And the sales agent is
01:53:46.239 there to give people a little bit of
01:53:47.920 information about what's in the course,
01:53:49.840 get them excited about what we're doing.
01:53:51.760 And then if they do want the course,
01:53:53.760 it's going to allow them to buy it. And
01:53:55.520 when they buy it, this is where we're
01:53:57.119 going to start to actually start to
01:53:59.199 interact with state. So whenever a
01:54:01.840 customer does purchase a course, this is
01:54:04.800 where we are going to update the state.
01:54:07.119 So let's look at what's in state first
01:54:08.560 and then we're going to come back to
01:54:09.599 purchase course. So at a high level what
01:54:12.239 we have inside a state are three
01:54:13.840 different keys. So we have username so
01:54:15.760 you know who's working and who we're
01:54:17.520 talking to. From there we have purchase
01:54:19.599 course. So this is where we can see what
01:54:21.360 courses the person has already accessed.
01:54:23.840 And a purchase course will always appear
01:54:26.480 in this structure where we have the
01:54:28.639 course ID. So this is going to be like
01:54:30.719 oh you've bought course number one or
01:54:32.480 course number two. And then also the
01:54:34.560 purchase date. The purchase date is
01:54:36.239 super important because if the person
01:54:37.760 wants a refund, we can will 100% honor
01:54:40.239 that if it's been less than 30 days. So,
01:54:42.080 let's go back to the purchase course.
01:54:43.840 So, if someone does try to purchase a
01:54:46.080 course, what we'll do is go, okay,
01:54:48.159 great. You want to buy this course?
01:54:50.080 Well, what we'll do is it looks like you
01:54:51.840 do not have any purchase courses in
01:54:53.920 state. So, I will happily buy this for
01:54:55.679 you, charge you the the $150, and then
01:54:58.400 from there, I will update the state so I
01:55:00.480 know in the future if you have any
01:55:02.320 questions that you have access to this
01:55:04.320 course. If we for whatever reason
01:55:06.159 already have access to this course, like
01:55:08.239 we bought it in the past, the agent's
01:55:09.760 going to go, "Oh, it looks like you
01:55:11.040 already own this. You can't buy it
01:55:12.480 again." So, just uh we're gonna have
01:55:14.000 some nice logic in our prompts to help
01:55:15.520 make that happen. Now, from there, what
01:55:17.440 we have is our course support agent. Our
01:55:19.679 course support agent always looks to see
01:55:22.159 which purchase courses we've made so far
01:55:24.719 and then it can answer questions about
01:55:26.159 them. So, for example, once you buy the
01:55:28.639 course, it's going to say, "Okay, I can
01:55:31.199 now help you answer any questions about
01:55:33.119 any of the modules inside the course."
01:55:35.280 We don't want to give away too much
01:55:36.560 information about like what's happening
01:55:38.320 in every single lesson and module inside
01:55:41.360 of the course until people buy it. So,
01:55:43.360 that's why this agent checks to see,
01:55:45.440 hey, have you bought it? If so, great. I
01:55:47.440 can answer any question and help you
01:55:49.280 through any problem inside the course.
01:55:51.040 So, this is a pretty cool one. And then
01:55:53.040 finally, if people do uh want to get a
01:55:55.840 refund, they'll be directed over to the
01:55:57.760 order agent. And the order agent has one
01:56:00.320 job, which is to allow people to get
01:56:02.480 refunds on their courses. So, whenever
01:56:04.400 someone does want a refund, what'll
01:56:05.840 happen is we'll check to see if they
01:56:07.520 first own the course. And if they do,
01:56:09.679 great. If they uh what we'll do is we
01:56:12.000 will refund them, send them their money
01:56:13.360 back, and we will drop the purchase
01:56:15.920 course from state. So, this is kind of
01:56:18.159 how multi-state systems work to where
01:56:20.639 just a quick recap of why this is so
01:56:22.320 awesome is we're now sharing state
01:56:25.119 between all of our different agents and
01:56:27.520 depending on the state, these agents
01:56:29.920 behave differently. So, quick recap.
01:56:31.840 Sales agent will buy the course if it's
01:56:34.000 brand new. If they don't already own it,
01:56:36.159 if they do own it, we'll say, "Nope, you
01:56:37.920 can't buy it again." The course support
01:56:39.840 agent is going to go, "Hey, do you have
01:56:42.159 access to this agent?" Great. I can
01:56:44.159 answer questions. Do you not purchase
01:56:46.000 this course already? Great. I will not
01:56:47.920 be able to answer those questions yet,
01:56:49.760 but if you would like to purchase it,
01:56:51.119 great. I'll refer you over to the sales
01:56:53.040 agent. And then finally, the order agent
01:56:55.520 will say, "Hey, you have access to this
01:56:57.760 course. I can refund it to you." Or
01:56:59.520 it'll say, "Hey, you don't have access
01:57:01.280 to this course. You haven't bought it. I
01:57:02.639 cannot give you a refund." Okay, that is
01:57:04.880 our first multi- aent system at a high
01:57:07.599 level. Hope this kind of makes sense.
01:57:09.440 But what we'll do is we're now going to
01:57:10.880 dive into the code so you can see how
01:57:12.560 each one of these agents is actually
01:57:14.800 interfacing with state, making changes
01:57:17.119 to state, and you're going to see some
01:57:18.960 more prompt engineering to get all of
01:57:20.719 these different agents working properly,
01:57:23.119 specifically when it comes to using
01:57:24.639 tools to manage state. So, let's hop in
01:57:26.560 so you can see all of this in action
01:57:28.159 inside of our code. All right, so now
01:57:29.760 it's time for us to dive into the code
01:57:31.599 portion of our multi- aent system. And
01:57:34.239 what we're going to do in this second
01:57:36.239 part is walk through everything step by
01:57:38.800 step because I want to make this as easy
01:57:40.320 as follow as possible. So first things
01:57:42.320 first, we're going to look at our
01:57:43.520 main.py because this is where we have
01:57:45.199 all of our core logic for creating our
01:57:47.440 sessions, creating our runner and then
01:57:49.440 actually handling user queries. And once
01:57:51.599 we understand quick recap of all of
01:57:53.360 that, we're going to dive into looking
01:57:55.440 at the core agents that are running
01:57:57.760 everything inside of our application.
01:57:59.360 So, we're going to look at our root
01:58:00.400 agent and we're going to look at all the
01:58:02.080 sub aents with their prompts and tools
01:58:04.000 so you can understand how everything is
01:58:05.679 working together when it comes to
01:58:07.599 answering user queries, updating state
01:58:09.679 so that you can master multi- aent
01:58:11.760 systems. So, we're going to speed
01:58:12.960 through the main.py because a lot of
01:58:14.400 this is just a recap from what you've
01:58:15.840 seen before and we're going to focus
01:58:17.440 most of our time inside of these sub
01:58:19.360 aents. So first things first is we are
01:58:21.599 going to create an in-memory session
01:58:23.280 service like we've done to where we're
01:58:24.960 going to save state just locally on our
01:58:26.880 computer just for testing purposes.
01:58:29.199 We're going to create our initial state
01:58:31.280 where we're going to say hey you are
01:58:32.639 working with user Brandon Hancock. He
01:58:35.360 hasn't purchased any courses yet and he
01:58:37.520 hasn't made any conversations yet. We're
01:58:39.040 just starting from scratch. From there
01:58:41.119 we are going to create a new session
01:58:43.040 where we're going to say you are a part
01:58:45.440 of the app name customer support and
01:58:48.239 this conversation you're working on
01:58:49.920 belongs to user ID AI with Brandon and
01:58:53.199 we're going to pass in the initial
01:58:54.480 state. From there we are going to create
01:58:57.119 our runner like we've done multiple
01:58:58.880 times in the past where we pass in two
01:59:00.719 raw ingredients the agent and then the
01:59:03.599 session service. And then once we have
01:59:06.000 our runner created, we're now ready to
01:59:08.239 start interacting with our users. And
01:59:10.960 this is just a simple everything from
01:59:13.040 this part onward is basically us
01:59:15.280 allowing our users to type in a request
01:59:17.920 to us, us capture that request, and then
01:59:20.080 send it to our runner. That's pretty
01:59:21.360 much everything that's happening here.
01:59:23.040 And outside of that, there's just a
01:59:24.320 bunch of logs. So most of the code
01:59:26.159 you're seeing after this point is just
01:59:28.159 adding a ton of logs to show off to our
01:59:30.800 final users of what's actually happening
01:59:32.560 inside the application. So long story
01:59:34.639 short, we're saying great, give me your
01:59:37.199 input. I will take in that input and I
01:59:40.159 will pass it over to the agent. Once I
01:59:43.119 pass it over to the agent, what I'm
01:59:45.199 trying to do is just most of this is
01:59:46.880 logs. So most of this is not necessary.
01:59:49.280 I just wanted to make it super easy for
01:59:50.880 you to see everything that's happening
01:59:52.800 once we start to run the code. But the
01:59:54.960 most important part is right here where
01:59:56.800 we're going to go, okay, great. I now
01:59:59.040 have the new message you gave me and I'm
02:00:01.599 going to basically call run async where
02:00:04.320 run async goes all right I now have the
02:00:07.599 user I know the session and the new
02:00:09.679 message I'm going to pass everything
02:00:10.960 over to the agent so that it can
02:00:12.880 understand what response it needs to
02:00:14.719 generate who the agent needs to delegate
02:00:16.800 work to in order to give us a proper
02:00:18.480 response from there we're going to
02:00:20.880 process the agent response which is
02:00:23.119 mostly once again just logging
02:00:24.880 statements where we're going okay great
02:00:26.719 I know what the agent agent said and I
02:00:29.920 like I said 99% of this is just log
02:00:32.560 statements because most of the actual
02:00:34.719 work is already being handled when you
02:00:36.320 called run async. So we're just trying
02:00:37.920 to like hey is this the final response?
02:00:40.159 Great. I will happily log everything so
02:00:42.719 it's easy to view. So I'm going to skip
02:00:45.280 through most of this because most of it
02:00:47.119 you've already seen in the past. So
02:00:48.719 let's actually dive over to looking at
02:00:50.719 our core agent which is in the root
02:00:52.960 folder of our customer service folder.
02:00:55.119 And you can see we have a root customer
02:00:57.360 service agent. So let's walk through
02:00:58.880 what's going on in this agent and how
02:01:00.960 it's delegating work to its sub agent.
02:01:02.880 So at a high level we're need to give it
02:01:04.639 a description so it understands what
02:01:06.159 this agent does. And basically it's just
02:01:08.400 the root customer service agent for the
02:01:10.800 community I'm building. And from there
02:01:12.880 what you can see is it has core
02:01:14.960 instructions. And most of the questions
02:01:17.760 that this is supposed to help with is to
02:01:19.920 help the user with any questions and
02:01:22.400 then always direct them over to the
02:01:24.400 specialized agent who can handle this
02:01:26.480 response. So the core things that you
02:01:28.639 should be doing are you know
02:01:30.480 understanding what the user asks and
02:01:32.560 then route them to this appropriate
02:01:34.480 user. And to help the root agent better
02:01:37.679 understand what the current state of the
02:01:39.760 application is is we are going to pass
02:01:42.719 in the three different state values that
02:01:45.679 we have where we're going to say hey the
02:01:47.920 username is username. Here's all the
02:01:50.719 courses they've purchased so far and
02:01:53.040 outside of that here are all the core
02:01:55.040 events that have happened when working
02:01:57.199 with this agent. Now, now that you have
02:01:59.760 access to all that information, here's
02:02:01.520 how you can access and pass along over
02:02:04.400 to the appropriate agents that you have
02:02:06.560 access to. So, first things first, you
02:02:08.639 have access to the policy agent. And
02:02:10.560 here's what the policy agent is good
02:02:12.400 for. Mostly just answering questions
02:02:14.320 about customer support, course policy,
02:02:16.639 and refunds. The sales agent is for
02:02:19.360 answering any questions about making
02:02:21.400 purchases. And you can see the current
02:02:23.360 price of it. Finally, if someone has a
02:02:25.920 question about a specific topic within a
02:02:29.040 course, you're going to send them to the
02:02:30.639 course support agent. And you can only
02:02:32.880 do this if the user has purchased the
02:02:35.599 course. And what's great is because up
02:02:38.239 top, we've already told the agent what
02:02:40.639 courses the person has purchased. It's
02:02:42.320 obviously going to know, oh yeah, I
02:02:43.520 can't even direct a user over to this
02:02:46.239 agent if they haven't purchased a
02:02:47.840 course. And then finally, what we're
02:02:49.760 going to do is if anyone has any
02:02:51.280 questions about purchase history or
02:02:52.960 refunds, we'll send them over to the
02:02:54.719 order agent. So, as you can see, most of
02:02:56.800 the instructions at the root level are
02:02:58.480 all about delegation and briefly
02:03:00.320 explaining what all the underlying
02:03:02.239 agents do and when we should call on
02:03:04.320 them. So, it's a lot of instruction
02:03:05.840 giving. From there, the core part that
02:03:08.000 you'll notice is we've just given it
02:03:09.599 access to the four sub agents that it
02:03:11.920 has access to. So, let's dive through
02:03:13.599 each one of these one at a time. So,
02:03:15.520 first things first, we're going to look
02:03:16.560 at the policy agent. And think of this
02:03:18.480 one as almost like a rag agent to where
02:03:20.480 it's basically just like, "Hey, you have
02:03:22.000 a question? Cool. I'll look at the
02:03:23.280 policies we have and generate an
02:03:24.880 answer." So, you can see it's just a ton
02:03:27.360 of policy questions of like, "No
02:03:29.480 self-promotion, here's the behavior you
02:03:31.520 need to have, here's some policy on
02:03:33.719 refunds, here are access to, you know,
02:03:36.480 course access." It's basically just a
02:03:38.159 bunch of like general Q&A questions. So,
02:03:40.080 this is super helpful. definitely
02:03:41.520 recommend you stealing inspiration for
02:03:42.800 this as you go off and build your own
02:03:44.159 real world agents. Now, let's go look at
02:03:46.000 the sales agent because this is where
02:03:47.360 things start to get fun where we begin
02:03:49.760 to allow agents to update state and
02:03:52.880 start to purchase courses. So, the sales
02:03:55.040 agent, you know, hey, you are a sales
02:03:57.040 agent. Here is all the current
02:03:59.119 information about the current user. And
02:04:01.360 here is the course that you are trying
02:04:03.360 to sell. It is a full stack AI marketing
02:04:05.360 course. It's
02:04:06.599 $150. Here's what's included in the
02:04:08.800 course. And here's what the user will
02:04:10.080 learn when interacting with the user.
02:04:13.199 You know, please check to see if they
02:04:15.119 already own the course. If they do own
02:04:17.280 it, remind them they have access to it.
02:04:19.599 If they don't have access to the course,
02:04:21.679 just briefly explain the value
02:04:23.360 proposition of the course and ask them
02:04:25.360 if they want to purchase it. Then after
02:04:27.679 they have purchased the course, what
02:04:29.599 you'll do is track the interaction. So
02:04:32.000 we'll update event history and then
02:04:34.159 basically be ready to hand off the
02:04:35.840 course to support because once they
02:04:37.280 purchase the course we need to be able
02:04:38.560 to answer questions about it. So that's
02:04:40.320 this at a high level. And if the user
02:04:42.000 does want to purchase a course here is
02:04:44.000 what will happen. So first things first
02:04:46.159 is we have to pass in tool context
02:04:48.239 because in order for our tool to update
02:04:51.119 state we need to pass in tool context.
02:04:54.480 And what we can do is first look at to
02:04:57.360 see all right what inside of state what
02:05:01.360 courses has this user purchased and we
02:05:04.159 need to pass in a default value. So in
02:05:05.840 case for whatever reason this value in
02:05:07.599 state is blank. You always want to have
02:05:09.440 a fallback value. So this could if if we
02:05:12.400 were working with something else this
02:05:13.679 could be a blank like no courses but in
02:05:16.480 our case we're we're storing all of our
02:05:18.239 courses in a list. So that's why we're
02:05:20.000 putting it in a list. From there, what
02:05:21.440 we're doing is some simple Python logic
02:05:23.520 to say, okay, I would like to iterate
02:05:25.920 through all of the different courses
02:05:28.480 that the user has purchased to check to
02:05:30.639 see if the course ID basically I'm just
02:05:33.360 trying to get all the course IDs. And
02:05:35.280 then from there, what I'm trying to
02:05:36.639 check to see is like, okay, has the user
02:05:39.199 purchased this course ID? So, we're
02:05:40.960 saying if this course ID is in the list
02:05:44.239 of course IDs we have, what we're going
02:05:46.800 to do is say, hey, you already own this
02:05:48.880 course. You can't buy it again. So
02:05:50.480 that's what that logic says. Then what
02:05:52.320 we're trying to do next is we're going
02:05:54.239 to go great. So we've made it this far.
02:05:56.080 We know they don't have access to the
02:05:57.679 course. So now what we're going to do is
02:05:59.679 purchase the course. So what we're going
02:06:01.599 to do is we're making a new list where
02:06:04.400 we're going to iterate through all their
02:06:05.840 existing courses and continually add the
02:06:08.880 existing courses to the list. And then
02:06:11.440 finally, what we're going to do is add
02:06:12.880 the new course we've just purchased for
02:06:14.639 them to the list. And then once we have
02:06:17.679 the new state up and ready, we're going
02:06:19.920 to save it to the state that's shared
02:06:21.920 amongst all the agents. So quick recap,
02:06:24.400 what we're doing in this logic right
02:06:26.480 here is saying, great, I'm updating your
02:06:30.320 list of courses you own with a new one.
02:06:32.480 And once we have the proper updated list
02:06:35.440 of all the courses you've bought, we're
02:06:37.440 then going to save the updated list to
02:06:40.000 state. That's all we're doing right
02:06:41.199 here. And we're also going to update
02:06:43.280 your interaction history to say, hey,
02:06:46.079 you purchased this course at this
02:06:48.719 timestamp so that we have a history of
02:06:51.440 all key events when working with this
02:06:54.000 agent and specifically so that when
02:06:56.000 other agents are looking at what's
02:06:57.520 happened so far, they can easily look at
02:06:59.280 the interaction history. All right.
02:07:01.119 Finally, from there, we are going to
02:07:02.800 follow tool best practices where we are
02:07:05.520 going to update and return state. So
02:07:08.320 state instead of just saying, "Hey,
02:07:10.400 true, we purchased it." No, we follow
02:07:12.400 best practices where we give status, we
02:07:14.800 give a message, and we properly say,
02:07:16.960 "Here's what you bought in at this time
02:07:18.560 stamp." So that was a little bit of a
02:07:19.840 deep dive, but hopefully you got to see
02:07:21.040 a lot of the core principles of how
02:07:22.400 we're passing in state dynamically, how
02:07:24.800 we are following best practices and
02:07:27.840 allowing our tools to access state
02:07:30.320 through tool context, and how we are
02:07:32.960 reading from state. And then from there,
02:07:35.280 you're seeing how we are saving back to
02:07:38.079 state. So you're seeing, you know,
02:07:39.760 you're becoming a master of all the core
02:07:41.520 components of working with multi- aent
02:07:43.280 systems and following best practices
02:07:45.119 with tool calls. Okay, we are almost
02:07:47.360 done reviewing this. So let's look at
02:07:49.280 the core support agent and we'll speed
02:07:51.199 through these cuz the rest of these are
02:07:52.560 pretty much just instruction heavy. So
02:07:54.719 at this point, per usual, we're passing
02:07:56.639 in state into this agent so it knows
02:07:59.119 exactly what's going on. And then based
02:08:01.679 on what courses the person has
02:08:03.920 purchased, we then can answer questions
02:08:07.159 appropriately. So if the user owns the
02:08:09.840 course, great. What we'll do is help
02:08:12.400 them with the course. Cuz if they own
02:08:14.079 it, we can answer questions about it. If
02:08:15.760 they don't own the course, we're going
02:08:17.040 to direct them over to the sales agent.
02:08:18.560 So the sales agent can say, "Hey, you
02:08:20.320 don't own this, but it looks like you're
02:08:21.440 interested in it. I'd be happy to answer
02:08:23.440 questions. you just got to buy it first.
02:08:25.040 So then what I do is then just give a
02:08:27.199 ton of information about the course. So
02:08:29.040 I say, "Hey, in section one, here's what
02:08:30.800 you learn. In section two, here's what
02:08:32.239 you learn." And I just keep going
02:08:33.840 throughout the rest of the course so
02:08:35.520 that there's some highle overview of
02:08:37.119 what's being included in the course.
02:08:39.679 Finally, the last agent is the order
02:08:41.599 agent. And the whole purpose of the
02:08:43.280 order agent is to allow persons to ask
02:08:46.079 questions about the purchase history and
02:08:47.840 process refunds. So what we're doing is
02:08:50.320 giving all the state per usual.
02:08:52.159 Hopefully, you're starting to see the
02:08:53.520 core principles seeing used over and
02:08:55.520 over and over again. And then what we're
02:08:57.040 trying to do here is just say, "Hey, if
02:08:58.560 they ask about the purchases, just let
02:09:00.480 them know what they've purchased. If
02:09:02.239 they want to refund, what you need to
02:09:04.079 do, verify that they own it, and then
02:09:06.159 from there, if they do own it, give them
02:09:08.320 a refund if it's been under 30 days. So,
02:09:10.800 yeah, that's pretty much all we're doing
02:09:12.880 inside of our agents. And if they do get
02:09:16.079 a refund and things go through
02:09:17.520 successfully, what we're trying to do,
02:09:19.520 per usual, the exact same thing what we
02:09:21.199 did with the order call a second ago,
02:09:23.599 the order tool call, but now we're just
02:09:25.520 undoing it. So undoing it follows the
02:09:27.920 exact same process at a high level. You
02:09:30.079 get state, you check just to confirm to
02:09:32.639 make sure they own it. If they do own
02:09:34.880 it, what we're going to do is remove the
02:09:37.119 course from the list. Once we've removed
02:09:39.840 the course from the purchased course
02:09:42.000 list, we're going to update state. We're
02:09:44.239 going to update our interaction history
02:09:46.800 to say great, it looks like we did get a
02:09:50.079 refund. So that's what we're updating
02:09:51.599 our interaction history with, saying
02:09:53.040 they refunded the course at this time.
02:09:55.440 And we're saving it back to state. And
02:09:57.360 then we're returning the tool call to
02:09:59.199 say, yep, this was a success. They
02:10:01.840 refunded the course and here's some
02:10:03.440 additional information. Okay, so you now
02:10:05.520 got to see all the core parts of this in
02:10:07.760 action. So what we're going to do is now
02:10:09.280 that you've gone through and seen
02:10:10.719 everything, understand part by part from
02:10:13.280 prompts to tool calls to tools updating
02:10:15.520 state. So what we're going to see now is
02:10:17.280 we're going to go off and run this so
02:10:19.920 you can see exactly how all of these
02:10:22.159 works together. So let's kick everything
02:10:23.840 off and start running the demo. All
02:10:25.360 right, so now let's dive into the fun
02:10:26.880 stuff where we're going to run our
02:10:28.560 agents. And as a quick reminder, you
02:10:30.079 need to be in folder number eight so you
02:10:32.400 can run this example and you need to
02:10:34.239 have your virtual environment activated.
02:10:36.159 Once you've done both of those, we can
02:10:37.760 run everything. So, type in Python
02:10:39.760 main.py and this will create your
02:10:41.599 session. It'll get everything set up and
02:10:43.599 ready to run. So, we can now say, "Hey,
02:10:46.719 what courses do you have for sale?" Now,
02:10:50.320 what this will do is spit out a ton of
02:10:52.400 logs so you can see everything that's
02:10:53.920 happening. So, you can see we always
02:10:55.199 have a before state and an after state
02:10:57.760 so you can see exactly what's happening.
02:11:00.000 And right here in the blue in the
02:11:02.000 middle, you can see the agent response.
02:11:04.000 So you can see it goes okay great I have
02:11:06.320 a course available it's priced at this
02:11:08.400 amount of money and you can see that the
02:11:10.239 customer service agent gave us this
02:11:11.920 response so we can say yes I would like
02:11:14.719 to purchase that
02:11:17.400 purchase that course from there what
02:11:20.159 will happen is we will be sent over to
02:11:22.320 the sales agent who's responsible for
02:11:24.000 closing the sale and we goes great I can
02:11:26.159 help with that here's the course it's a
02:11:27.760 sixe program the price is this would you
02:11:29.920 like to proceed with the purchase yes
02:11:32.000 please purchase
02:11:34.079 the course. From there, what will happen
02:11:37.199 is you can start to see we make some
02:11:38.880 state changes. So, before saying I'd
02:11:41.440 like to buy the course, we didn't have
02:11:43.040 access to it. Afterwards, though, you
02:11:44.800 can see the agent said, great, you
02:11:46.480 successfully bought it. You're enrolled.
02:11:48.480 Would you like to start learning? And
02:11:49.760 you can see that our state after running
02:11:52.159 this request now has the course. So,
02:11:54.480 awesome. We now have our agents managing
02:11:56.960 our state through tools. Really cool. So
02:12:00.000 now we can say yes, what are all the
02:12:03.199 modules inside of the program? From
02:12:06.480 there, what will happen is we should be
02:12:08.480 directed over to the course support
02:12:10.880 agent. Yep. Course support agent. And
02:12:13.520 the agent will say, "Okay, yep. Because
02:12:15.760 you have access to all of the because
02:12:18.400 you've purchased this course, I can give
02:12:19.679 you answers now. You bought it on this
02:12:21.599 date and here are all the different
02:12:23.119 modules. Do you have any questions about
02:12:24.560 anything in particular?" And we could
02:12:26.000 dive in. But in our case, we're going to
02:12:27.440 say, "No, I'm good. I don't want the
02:12:32.239 course any more. Give me a full refund."
02:12:36.719 And what this should do is move us over
02:12:39.040 to our support agent. So, what you can
02:12:42.320 see here is our before state shows that
02:12:45.199 we have access to the course. Then, we
02:12:48.400 should get delegated over to the proper
02:12:50.639 agent. In our case, it's going to be the
02:12:52.239 order agent. and it'll go great I have
02:12:55.360 refunded your course completely the
02:12:58.159 money will be sent back to your account
02:12:59.360 in three to five days and you've been
02:13:01.280 remove the course has been removed from
02:13:02.719 your account and what's awesome is you
02:13:04.400 can now see our course has been removed
02:13:06.480 from state so our order agent properly
02:13:08.400 removed the course so yeah so this was a
02:13:10.639 quick overview guys of showing you how
02:13:12.560 multi- aent systems can work together
02:13:14.560 and they can be more intelligent by
02:13:16.079 sharing state because when they share
02:13:17.840 state they can know exactly what you
02:13:19.440 have access to don't have access to and
02:13:21.440 respond appropriately so hopefully You
02:13:23.199 guys found this example super helpful
02:13:25.040 and now it's time for us to move over to
02:13:26.880 example number nine where we're going to
02:13:28.480 dive into callbacks so you can learn how
02:13:30.560 we can manage all sorts of interactions
02:13:33.199 between agents and LLN and have full
02:13:35.040 control over our agent workflows. So
02:13:36.800 let's hop over to example number nine.
02:13:38.480 Hey guys and welcome to example number
02:13:40.159 nine where you're going to learn about
02:13:41.360 the six different types of callbacks
02:13:43.360 that you can add to your agent workflows
02:13:45.360 to help you control every part of your
02:13:47.679 agentic systems. And there are six
02:13:50.159 different types of callbacks that we're
02:13:51.760 going to cover here throughout this
02:13:53.199 example. So the before and after agent
02:13:55.840 call back, the before and after model
02:13:58.239 call back, and the before and after tool
02:14:00.719 call back. So what we're going to do in
02:14:02.159 this example is first head over to the
02:14:04.000 doc so you can see what each one of
02:14:06.000 these different types of callbacks do
02:14:07.760 and some of the best practices. And then
02:14:09.520 from there, we're going to quickly cover
02:14:11.119 each of these different examples I
02:14:12.639 prepared for you guys and run them. So
02:14:14.320 this one's going to be a little bit more
02:14:15.360 interactive than the other examples. So
02:14:16.880 let's go ahead and hop over to the docs.
02:14:18.560 you can understand everything you need
02:14:19.840 to know about callbacks. All right, so
02:14:21.440 the first thing I want to show you guys
02:14:22.639 is this highle overview of when each of
02:14:25.360 the callbacks gets triggered inside of
02:14:27.520 ADK. So the first two callbacks that
02:14:30.159 you're going to see in use are going to
02:14:31.840 be the before and after agent call back.
02:14:34.880 These are going to be before any logic
02:14:37.440 happens inside of your AI solution. So
02:14:39.840 this is right when things get kicked
02:14:41.679 off. What do you want to do? And then
02:14:43.520 once everything is done being processed
02:14:45.679 with your agent, what do you want to do
02:14:47.440 with the information that you now have?
02:14:49.440 So that's the before and after callback.
02:14:51.520 And you're going to see some more
02:14:52.320 examples of these in just a minute. The
02:14:53.760 next callbacks I want to show you are
02:14:55.520 the model callbacks. So the before and
02:14:58.320 after model callbacks are going to be
02:15:00.480 used before you pass information over to
02:15:02.880 Gemini or OpenAI or Claude. What do you
02:15:05.840 want to do with the request you're
02:15:07.280 sending over to these models? So you can
02:15:09.199 do a little bit of pre-processing and
02:15:10.719 adding some information and you can do
02:15:12.560 some like validation or some checking
02:15:14.159 afterwards. Then finally we have before
02:15:16.719 and after tool call backs because our
02:15:19.760 agent has the ability to call tools such
02:15:21.760 as get the weather, get the stocks and
02:15:23.679 sometimes what you can do with these is
02:15:25.840 maybe add in some validation and add in
02:15:28.639 some additional information and then
02:15:30.800 once you get back results from the tool,
02:15:32.719 you can process it to make sure it
02:15:34.239 included the proper information. So,
02:15:35.760 these are the six different callbacks
02:15:37.119 we're going to be diving into. So, let's
02:15:38.960 head over to the doc so you can see some
02:15:41.360 of the core principles that ADK tells us
02:15:44.079 when and why we should use each one of
02:15:46.079 these callbacks. All right, so I've
02:15:47.520 zoomed everything in so we can easily
02:15:49.040 walk through the six different callbacks
02:15:51.199 and cover when and why you would want to
02:15:53.840 use these callbacks. So, to start off,
02:15:55.840 let's look at the before agent call
02:15:57.840 back. And this is the one I use the most
02:15:59.679 and you'll most likely use the most as
02:16:01.599 well as you work with ADK. And you know,
02:16:04.719 you saw the before agent call back is
02:16:07.040 triggered before anything gets called
02:16:09.119 inside of our agentic system. And the
02:16:12.079 main reason you'll want to use this
02:16:14.800 different callback is to set up
02:16:16.800 resources and state before the agent
02:16:20.000 runs. So this is where I like to do some
02:16:23.280 state hydration, which is just a fancy
02:16:25.199 word to say, hey, before this agent
02:16:27.040 runs, let's go fetch some information
02:16:28.880 about the user. So let's grab their
02:16:30.639 current order history. Let's go grab
02:16:33.040 whatever subscription they have and
02:16:35.120 let's just give all that information to
02:16:37.200 the agent so when it's running it has
02:16:38.879 everything it needs to know. So main
02:16:40.478 reason to use this one is for setup.
02:16:42.879 State setup is when I like to use this
02:16:45.519 one. Okay. Now the next one you're going
02:16:48.080 to be using is the after agent callback.
02:16:51.200 And this one runs after everything is
02:16:53.760 done. So you've you've made all the
02:16:55.519 requests to the LLM, you've done all the
02:16:57.439 tool calls, the agent's done running.
02:17:00.240 then the agent call back is triggered.
02:17:03.200 Now when and why would you want to use
02:17:05.200 this one? So their main options are for
02:17:08.160 postexecution validation and logging.
02:17:10.558 Those are the main ones I like to use.
02:17:12.638 So after the agent's done running, you
02:17:14.558 can just make some logs to if you have
02:17:16.879 this application running in production,
02:17:18.398 you can just make some additional logs
02:17:19.840 of like, hey, I gave the user this
02:17:22.318 information. So you can just really just
02:17:24.160 save it. That's the main one I like to
02:17:25.920 use it for. And if you want to modify
02:17:28.240 any state, so if you want to keep up
02:17:29.920 with the number of requests the user has
02:17:32.240 made, this is a great place to modify
02:17:34.080 state afterwards. Okay, the next one
02:17:36.879 we're going to look at is the before
02:17:38.959 model call back. Now the before model
02:17:40.799 call back, just remember this is before
02:17:42.799 we trigger OpenAI, Gemini, Claude,
02:17:46.000 whatever model we're working with, we
02:17:47.679 trigger this before we send the request
02:17:50.638 over to the large language model. Now,
02:17:53.040 when and why do we want to use this?
02:17:55.040 Well, a few different examples that ADK
02:17:58.240 recommends is for adding additional
02:18:00.160 dynamic instructions or injecting some
02:18:03.280 examples based on state or model
02:18:05.359 configurations. Now, I don't really use
02:18:07.840 this one that much, but what you could
02:18:09.760 do is also add in some guard rails. And
02:18:12.080 you'll see this in an example that we're
02:18:13.519 going to work on together, but you can
02:18:15.120 use Python to review the request we're
02:18:17.840 sending over to the large language model
02:18:19.280 to say like, hey, are they using any
02:18:21.040 profanity or are they doing anything
02:18:23.439 that's, you know, they shouldn't be
02:18:24.879 asking inside of our agent? And you can
02:18:26.718 just do a quick check to say, oh, they
02:18:28.398 are. Okay, I'm not going to allow the
02:18:30.799 user to send this request to the large
02:18:32.558 language model. This is not allowed. So
02:18:34.478 that's what we're going to be working on
02:18:35.760 together. And you're going to see later
02:18:37.599 in a second how you can, you know, quit
02:18:41.280 the the loop if the user tries to ask
02:18:43.519 for something that they're not allowed
02:18:44.718 to. So you can either yeah skip it
02:18:46.879 basically. So you're going to see that
02:18:47.920 in a second. Then the next one you can
02:18:49.599 see is after model call back. So once
02:18:53.040 Gemini or OpenAI gives us an answer,
02:18:55.519 what we can do is alter the information
02:18:58.879 given back to us. So that's one of the
02:19:00.799 main reasons I like to use the
02:19:02.799 aftermodel callback. it is to reformat
02:19:05.439 the response. So if there's any certain
02:19:06.959 words you don't want the agent to use,
02:19:09.200 you can actually replace keywords. You
02:19:11.280 can log anything you want or you can
02:19:13.679 censor or blur out information. So for
02:19:16.080 example, if the agent returned something
02:19:18.318 it wasn't supposed to, like maybe the
02:19:19.679 user's ID or anything like that, you
02:19:21.920 could actually blur it out so the user
02:19:23.920 can't see it. All right, the next two
02:19:26.000 that we're going to look at are going to
02:19:27.679 be tool execution callback methods,
02:19:30.080 specifically the before and after. So
02:19:32.318 the before tool callback, it does
02:19:34.638 exactly what it it says. It gets
02:19:36.000 triggered before the tool gets called.
02:19:37.920 And the main reason I like to use this
02:19:39.840 one are to basically inspect and modify
02:19:42.799 the tool arguments or perform
02:19:45.080 authorization. So, for example, if the
02:19:47.840 user was going to make a request to,
02:19:50.160 let's say, add an additional item or
02:19:52.080 purchase it, we could make sure that the
02:19:54.399 user ID that was making the request
02:19:57.040 actually matches the account that we're
02:19:58.960 working with to make sure nothing
02:20:00.240 weird's happening or they're not trying
02:20:02.000 to trick the LLM to make a tool call
02:20:03.920 they weren't supposed to. So, this is
02:20:05.439 when it comes down to authorization
02:20:07.120 checks. So, the other one that we can
02:20:09.040 start to work on is the after tool call
02:20:11.439 back. And the reason most of the time
02:20:13.359 people use this one is to really just
02:20:15.600 inspect, modify, and log the tour
02:20:18.720 results. So those are the main reasons
02:20:20.479 people use this one. So, but this one,
02:20:22.880 like I said, yeah, this one's not the
02:20:24.319 craziest. Or you could save information
02:20:26.319 to state. So these are all the six
02:20:28.479 different types of callbacks that you
02:20:29.840 can use highle purposes. But now what I
02:20:32.479 want to do is dive into the three
02:20:34.399 different examples I've set up for you
02:20:36.000 guys so you can see each one of these
02:20:38.240 callbacks in action at a high level and
02:20:41.359 understand how you can use them in your
02:20:43.280 code. So let's hop over to our cursor
02:20:45.680 and start seeing these callbacks in
02:20:47.280 action. All right, so now it's time to
02:20:48.640 get our hands dirty and dive into some
02:20:50.399 code. And we're going to walk through
02:20:52.240 each type of callbacks one at a time.
02:20:54.800 So, we're going to look at the code, run
02:20:56.000 it so you can see everything in action,
02:20:57.280 and we're going to iterate for each of
02:20:58.960 the different types before the agent
02:21:01.040 ones, the model ones, and the tool ones.
02:21:02.560 Let's go ahead and dive in to our before
02:21:04.720 and after agent callbacks. So, we're
02:21:07.200 going to open up our agent.py file for
02:21:09.280 this quick example. So, you can see the
02:21:11.760 before and after agent callbacks in
02:21:13.760 action. So, in order to add callbacks to
02:21:16.960 your agents, what you can do is update
02:21:20.000 the before and after agent callback.
02:21:21.840 like they make this so clear when it
02:21:23.600 comes to naming. And what you want to do
02:21:25.439 is for each one of these callbacks, you
02:21:27.439 want to point to a function. Now,
02:21:29.600 there's a few core things you need to
02:21:31.200 know about these functions before you
02:21:33.439 start to work with them. So, the first
02:21:35.040 thing is you need in order for callbacks
02:21:37.439 to work appropriately is you need to
02:21:39.520 pass in the callback context. This is
02:21:41.760 what's going to allow the agent to
02:21:43.200 access state and all the other necessary
02:21:44.960 information it needs to properly handle
02:21:46.960 what's going on. From there, you want to
02:21:49.120 make sure the return type is optional
02:21:51.520 and returning content. Now, what why why
02:21:54.080 are we doing this? Well, you'll see in
02:21:55.200 just a second. If you want the agent to
02:21:58.399 continue as normal, you return none. So,
02:22:01.200 that's why it's optional because we're
02:22:02.399 going to return none if everything's
02:22:03.680 okay. If for whatever reason the user
02:22:05.920 did something we didn't like, we would
02:22:08.000 return a message saying, "Hey, I'm
02:22:10.160 skipping this because of whatever
02:22:12.399 reason." So, you return none if things
02:22:14.399 go good. you return messages if you want
02:22:17.120 to skip what's happening. So that's uh
02:22:19.200 something that was a little weird to me
02:22:20.479 when I saw this for the first time. But
02:22:22.000 let's dive into this before and after
02:22:23.680 agent call back so you can see exactly
02:22:25.760 what we can do with these different
02:22:27.359 callbacks. So if you remember what we
02:22:29.600 want to do with the main reason we want
02:22:31.359 to use before agent callbacks is to log
02:22:33.920 and to hydrate state. So what you can
02:22:36.640 see is we're taking in the callback
02:22:38.640 context and the first thing we're doing
02:22:40.720 is we are grabbing state with state.
02:22:43.120 What we're doing is just to test out
02:22:45.439 some initial information is we are going
02:22:47.920 to say all right state do you have agent
02:22:50.640 name as a key if not I'm going to update
02:22:53.120 state to include the name and then from
02:22:54.720 there what we're going to do is we're
02:22:56.560 going to keep track of our request
02:22:58.640 counter so you can see hey does request
02:23:00.960 counter exist in state if not this is
02:23:03.120 obviously our first request otherwise
02:23:04.960 we're going to increase the state
02:23:06.560 request counter outside of that we're
02:23:08.640 going to add a third key to state where
02:23:11.840 we're going to keep track of the request
02:23:13.920 start time because in the after callback
02:23:16.479 agent we're going to see okay well you
02:23:18.800 started at this time and then you
02:23:20.240 finished at this time great I know it
02:23:22.000 took about 10 seconds 2 seconds 1 second
02:23:25.120 to generate this entire response outside
02:23:27.680 of that we're just going to do some
02:23:28.720 logging so we can see and keep track of
02:23:31.040 things as we run it awesome from there
02:23:33.200 you can see we have an after agent call
02:23:35.280 back who accesses the same call back
02:23:37.760 state and we're doing pretty much the
02:23:39.600 exact same thing so now we're going to
02:23:41.280 grab state Now, we're going to get the
02:23:43.359 current time. And then from there, we're
02:23:45.600 going to look at, okay, we're going to
02:23:47.520 grab the start time, and we're going to
02:23:49.520 subtract the current time from the
02:23:52.560 current time from the start time. And
02:23:54.160 this is how we get, oh, it took you 2
02:23:56.240 seconds to run this entire request. And
02:23:58.240 we're just going to log this all out.
02:24:00.560 So, enough talking about this at a high
02:24:02.399 level. Let's go ahead and run this root
02:24:04.960 agent so you can see it in action. So,
02:24:07.040 let's clear things out. Let's make sure
02:24:08.960 we are in example number nine. And if
02:24:11.040 you look in example number nine, there
02:24:12.960 are multiple folders and we want to go
02:24:15.439 to the before and after agent. So cd
02:24:18.000 before after agent. Great. Once we're
02:24:20.479 here, we can now run everything. So
02:24:22.240 we're going to type in adk web. And this
02:24:24.720 will trigger out the, you know, the web
02:24:26.720 interface that you're used to. And we'll
02:24:28.880 open it up. And what we can do here,
02:24:32.080 let's get everything running. So select
02:24:34.319 an agent. I think I did something wrong.
02:24:37.359 One second. So I made a quick mistake.
02:24:39.200 We should not have cded all the way into
02:24:42.000 these agents. We should just run the
02:24:43.840 program from the highle folder. So what
02:24:46.160 you need to do is just run adk web here.
02:24:48.960 And this will get everything kicked off
02:24:50.640 and going properly. So now you can see
02:24:53.040 it gives you the ability to select an
02:24:54.479 agent. And we're going to run the before
02:24:56.240 and after agent. So what we can do is
02:24:58.960 say
02:24:59.960 hey how are you doing? And this is just
02:25:03.200 going to showcase a few of the core
02:25:04.720 components that we have. So hey I'm
02:25:07.040 doing well. From there, we can say it's
02:25:09.600 doing well. And then if we dive into
02:25:11.200 state, you can see it saved all the
02:25:13.359 important information that we asked it
02:25:14.960 to do when it came to running an agent.
02:25:17.280 And we can say, what is your name? And
02:25:20.479 what we would expect this to do is to
02:25:22.160 update the request counter and the the
02:25:24.240 start time. And if we close out of this
02:25:26.560 session and hop back to our logs, you
02:25:29.120 can see because we had a bunch of logs,
02:25:31.280 you can see, oh, the second request took
02:25:33.840 60 seconds. And I can see if I go even
02:25:37.120 further up uh to call back number one,
02:25:39.840 you can see the first request took
02:25:41.600 almost 2 seconds. So you can see that
02:25:43.439 it's working and it's properly logging
02:25:45.680 everything that we showed. So now what
02:25:47.520 we're going to do is quit everything and
02:25:49.200 we are going to move over to the next
02:25:51.280 callbacks which are before and after
02:25:53.359 model. Okay, so now it's time for us to
02:25:55.760 look at the before and after model
02:25:57.920 callback example. So this is the
02:26:00.359 agent.py inside of this folder right
02:26:02.720 here. So, what we're trying to do inside
02:26:04.319 of this agent is showcase how you can
02:26:06.880 filter content. So, someone gives you a
02:26:08.960 request that you don't want, you can
02:26:10.479 quit and say, "Hey, that was a bad
02:26:12.319 request." And we're going to log
02:26:13.600 everything. Now, before we dive into
02:26:15.359 looking at these two different
02:26:16.960 callbacks, I want to show you guys how
02:26:18.880 easy it is to add them into your your
02:26:20.960 agents. So, instead of doing the before
02:26:23.920 and after agent callback, we now just
02:26:26.640 say before and after model call back. As
02:26:28.960 simple as that. And per usual, we just
02:26:31.040 pass in the callback function we want to
02:26:32.640 trigger. Now, here's what's different in
02:26:35.280 these new callbacks. Instead of only
02:26:38.560 providing the callback context, you also
02:26:40.880 need to provide the LM request where the
02:26:43.600 LLM request is going to include the
02:26:45.439 message that we are trying to send over
02:26:47.200 to Gemini or OpenAI. So, what you can
02:26:50.240 see is we can do exactly what we did
02:26:52.640 last time. we can pull out the state,
02:26:55.120 grab our agent name, and then from
02:26:57.200 there, what we're going to do is extract
02:26:59.359 the user's last message. And the reason
02:27:01.920 why we're trying to do that is we want
02:27:04.160 to iterate through all the message
02:27:06.080 content that was sent to us and we're
02:27:08.479 reversing the list so we can get the
02:27:09.840 newest item that's from the user. And
02:27:12.319 once we have that latest message from
02:27:14.720 the user, we're going to save it here.
02:27:16.640 Then what we're going to do is showcase
02:27:19.439 that. We're going to say if we have that
02:27:22.399 user message, what we want to do is just
02:27:24.720 showcase it. Then from there, what we're
02:27:27.520 going to do is say, all right, does that
02:27:30.000 latest user message include a bad word?
02:27:32.479 So, we're going to say, hey, does it
02:27:33.600 include the word sucks? If so, what
02:27:36.080 we're going to do is throw a bunch of
02:27:38.319 logs saying, hey, inappropriate content
02:27:40.319 was detected. And this is where we can
02:27:43.120 start to alter the life cycle of our
02:27:46.640 agents and our LLMs. So instead of
02:27:49.600 returning none, we're going to return an
02:27:52.479 LLM response. And this LLM response is
02:27:54.880 going to go, hey, you tried to make a
02:27:57.280 request and we're going to say, hey, I
02:28:00.160 cannot return like we're going to
02:28:01.920 basically instead of the LLM responding,
02:28:03.600 we're going to respond for it. So we're
02:28:05.439 going to say, hey, this model, we're
02:28:07.600 going to say, I cannot respond to this
02:28:09.040 message because it includes
02:28:10.319 inappropriate language. Please rephrase
02:28:12.399 your request without words like this.
02:28:14.399 Now, that was only if the message
02:28:17.200 included a bad word. If it did not
02:28:19.120 include a bad word, what we're going to
02:28:20.800 do is just return none because returning
02:28:24.080 with none just continues with the normal
02:28:26.319 life cycle. Then finally, what we're
02:28:28.240 going to do is with the other option,
02:28:31.040 which is the after model callback, all
02:28:33.439 we're going to do is do some simple
02:28:36.200 replacements. So, if the LLM responded
02:28:39.200 with something, we can actually change
02:28:40.880 the response. So, I'm going to scroll
02:28:42.960 down just so you guys can see it. So, if
02:28:45.040 for whatever reason the LLM responded
02:28:46.800 with an empty response, we're just going
02:28:48.080 to skip it. Otherwise, if the LLM does
02:28:50.880 include some text, we're going to say,
02:28:53.680 okay, what I would like to do is iterate
02:28:56.640 through all the words you said. And if
02:28:59.680 you included a word like problem or
02:29:01.680 difficult, I want to change the word
02:29:03.840 with challenge or complex. And then what
02:29:06.720 you can do is you go through the
02:29:08.800 original you go through the original
02:29:10.880 response that they gave us and we're
02:29:12.960 going to save it to modified text. So a
02:29:14.800 new variable and we're going to iterate
02:29:16.640 through each one of the words that we
02:29:19.040 want to replace. And we're going to
02:29:21.040 replace them inside of our text. And we
02:29:24.560 are going to return if if any of the
02:29:26.960 words included in our case problem or
02:29:29.600 difficult we are going to replace them.
02:29:32.160 And we are going to return our modified
02:29:35.120 answer. So if we replace something,
02:29:37.280 we're going to say modified true. And so
02:29:39.520 if we modified, we're going to say,
02:29:40.720 "Hey, I definitely did change something,
02:29:43.359 and I'm now going to return that LLM
02:29:46.399 response." That's all we're doing. If it
02:29:48.720 did not include a word we were trying to
02:29:50.080 replace, we're going to return none. So
02:29:52.319 that's all we're doing inside here. And
02:29:54.399 inside the readme, I actually have a few
02:29:56.160 different examples that you can test
02:29:58.000 things out with. So let's see. Down
02:30:00.399 here, I have some examples that you can
02:30:02.960 run. Let me show you guys really
02:30:05.120 quickly. Yeah. So to test model
02:30:06.880 callbacks, you can say this website
02:30:09.359 sucks. Can you help me fix it? So let's
02:30:11.200 go run everything so you can see these
02:30:12.800 in action. So let's run it again. So
02:30:16.000 we're going to do ADK web. This will
02:30:18.399 trigger our website to spin up. Now we
02:30:21.200 can go to the before and after model
02:30:23.200 session and we can type in this message.
02:30:25.600 This website sucks. Can you help me fix
02:30:27.359 it? And now the model's instantly going
02:30:29.840 to say, "Hey, I cannot respond to
02:30:31.520 messages when using words like suck." So
02:30:34.560 this is pretty much just exactly what we
02:30:36.560 told it to do. So if you were to hop
02:30:38.399 back over to our code, you can see this
02:30:41.200 is the exact message we said to do right
02:30:43.520 here. I cannot use respond with messages
02:30:45.439 like that. Okay, cool. So now let's try
02:30:47.840 out the other one. So we can say, what's
02:30:49.439 the biggest problem with machine
02:30:50.479 learning today? So we can now try this
02:30:53.040 example. So, we're going to open it up
02:30:55.280 and we would expect it to replace the
02:30:56.960 word like we told it to. We would expect
02:30:59.600 it to replace phrases like problem with
02:31:02.319 challenge. So, let's open everything up.
02:31:04.880 And now inside the before and after
02:31:07.120 model call back, if I was to send this
02:31:09.680 request in, instead of it saying
02:31:11.920 challenge, it will get replaced. And I
02:31:14.319 believe we can. Yeah. So, we can dig in
02:31:17.600 to the response. So, one of the biggest
02:31:19.760 So, this is what the model responded to.
02:31:21.840 It responded with one of the biggest
02:31:23.600 challenges or one of the biggest
02:31:25.200 problems with machine learning is that
02:31:27.200 it's data bias. But what you'll notice
02:31:29.520 is the LLM responded with the word
02:31:31.520 problem, but because we updated the
02:31:34.000 model after callback, we said, "Hey, use
02:31:36.479 the word challenge here." So you can see
02:31:38.160 it is it's working in real time. So this
02:31:39.840 is a cool way if you want to like make
02:31:41.280 sure you speak always in a certain way,
02:31:43.040 you can alter the response or filter out
02:31:45.040 something. If they give you an API key
02:31:46.720 or something that you shouldn't show
02:31:47.920 back to the user, you can always filter
02:31:49.359 it out. Okay, cool. So you now got to
02:31:51.439 see before and after model call backs in
02:31:54.240 action. So now what we can do is go over
02:31:56.720 to the final call back which is the tool
02:31:59.359 before and after callbacks. So let's hop
02:32:01.040 over there so you can see this one in
02:32:02.560 action. Okay, so it's time for us to
02:32:04.240 look at our final example which is going
02:32:06.479 to be the before and after tool
02:32:08.399 callbacks. And for this example, we are
02:32:11.040 building an agent that looks up the
02:32:12.880 capital cities of different countries.
02:32:14.560 And because we're working with the
02:32:16.399 before and after tool callback, well, we
02:32:18.880 obviously need to have a tool that we're
02:32:21.359 trying to alter the functionality of for
02:32:23.520 these before and after capabilities. So,
02:32:26.319 what I'd like to do is first just show
02:32:27.680 you the tool we're trying to use and
02:32:29.359 then we're going to walk through what
02:32:30.560 we're trying to alter in these
02:32:31.680 callbacks. Okay. So, what tool are we
02:32:33.840 trying to use? Well, we're creating a
02:32:35.359 tool that takes in a country and once it
02:32:37.920 takes in a country, it looks up to see
02:32:40.240 does that country exist in here? And if
02:32:42.880 so, I'm going to return the capital
02:32:44.960 city. So yeah, that's what the tool is
02:32:46.800 trying to do at a high level. Super
02:32:48.720 straightforward. But now let's first
02:32:50.720 dive into the before tool call back so
02:32:52.640 you can see it in action. So the before
02:32:54.720 tool call back has a few key parameters
02:32:57.200 you have to pass in. The first is the
02:32:59.280 tool. What tool are we trying to use?
02:33:01.840 From there, we need to know what
02:33:03.359 arguments we're passing into that tool.
02:33:05.520 And then finally, the tool context. So
02:33:07.520 this is how we access state like in all
02:33:09.680 the previous examples. So in this
02:33:11.439 example, we're trying to do two
02:33:12.880 different things. First, if the user
02:33:15.520 gives us uses the tool get capital city
02:33:19.040 and they pass in an argument such as
02:33:21.680 America, we want to alter that argument
02:33:25.680 to say United States. So we're basically
02:33:27.600 correcting the arguments that a user
02:33:29.840 passes to us. And we're going to return
02:33:32.000 none because return none just means
02:33:33.760 proceed as you normally would. But the
02:33:35.920 kick is we have altered an argument
02:33:38.560 passed in. Another option is if the user
02:33:42.399 calls get capital city tool and the
02:33:44.960 country they pass in is restricted. What
02:33:47.600 I want to do is alter this tool call to
02:33:51.280 return this result. So we're not going
02:33:53.200 to call the tool. We're canceling the
02:33:55.120 tool call before it happens and just
02:33:56.960 returning this result. So that's exactly
02:33:59.040 what we're trying to do with the before
02:34:00.720 tool call back. So what we can do is run
02:34:03.439 this so we can see it in action. So
02:34:05.200 let's get everything ready. So we are
02:34:07.359 going to do ADK web and we are going to
02:34:10.479 open up our before and after tool and we
02:34:14.399 can say what is the capital of America
02:34:18.960 and what it'll do is it will get the
02:34:21.120 capital city and it will return the
02:34:23.520 capital city and it'll say oh it was
02:34:25.359 Washington DC. Now if you look here what
02:34:29.200 happened though is we actually made some
02:34:31.600 changes and you can't see the changes
02:34:33.120 inside ADK web. you have to hop back to
02:34:36.560 our terminal and inside of our terminal
02:34:38.800 we had some raw logs set. So you can see
02:34:42.240 the user passed in what's the capital
02:34:44.240 city of America but then before the tool
02:34:47.120 got called right here. So function call
02:34:49.920 you can see we updated the arguments to
02:34:52.319 now say United States and because
02:34:54.640 normally it would have just passed in
02:34:56.000 America but we altered it to pass in
02:34:58.960 United States. So pretty cool that it
02:35:01.439 did that. Now let's go try the other
02:35:03.600 example. So in our case, the other
02:35:05.600 example we wanted to try was if they
02:35:07.760 asked about restricted. So let's open
02:35:09.920 this up and we can say on our before and
02:35:12.479 after tool call, what is the capital of
02:35:15.880 restricted? And in this case, it's going
02:35:18.240 to return like, hey, I can't fulfill
02:35:20.080 that request. You know, not valid.
02:35:21.920 Please return a valid country. But if we
02:35:24.160 were to do a normal country, so like
02:35:25.680 what is
02:35:27.240 the capital of let's just do France,
02:35:31.359 this would work nor like normal like it
02:35:33.280 was supposed to do and it would go off
02:35:36.160 and say, "Yep, the country is France.
02:35:38.080 I'm calling this tool and then I got
02:35:40.000 back the answer which is Paris." So
02:35:41.840 yeah, we have the before functionality
02:35:43.760 working like a champ. So now let's
02:35:46.240 quickly review the after call toolback.
02:35:49.760 So when it comes to the after tool call
02:35:52.000 back, this is where we can alter the
02:35:54.240 tool response. That's the main
02:35:55.840 functionality of altering the tool call
02:35:58.479 back. So what you can see is we're just
02:36:00.319 doing a bunch of logs to say like, hey,
02:36:02.240 what tool got called? What were the
02:36:03.840 initial arguments passed in? And what
02:36:05.439 was the original response of the tool?
02:36:08.479 Then from there, what we can do is make
02:36:11.280 some changes. Oh, and before we do that,
02:36:12.960 I do just want to call out the
02:36:14.160 properties. you do need to pass in the
02:36:16.160 tool that's getting used, the arguments
02:36:17.840 that were passed to the tool and then
02:36:19.680 tool context and tool response. These
02:36:22.080 are the main ones. So the only one that
02:36:23.600 got added new was the tool response
02:36:25.280 because obviously the tool generated a
02:36:26.880 result. So we now have the opportunity
02:36:28.720 to alter it. So what we're going to do
02:36:30.800 is we're going to say all right if the
02:36:32.800 user basically passed in so if the tool
02:36:35.760 let me restate this if the tool get
02:36:38.160 capital city was called and Washington
02:36:40.640 DC was in the original result what we
02:36:43.920 want to do is alter that response to say
02:36:47.760 okay I want the modified result that I'm
02:36:51.280 storing here to say okay the answer was
02:36:54.319 Washington DC and then we're going to
02:36:56.160 add this fancy little note at the end so
02:36:57.920 we have a nice little emoji So that's
02:36:59.680 all we're doing. We're just long story
02:37:01.280 short for all of this code right here is
02:37:03.200 we're just altering the original
02:37:05.120 response that was given to us to include
02:37:07.520 the original result and then add in some
02:37:09.280 additional text at the end. So let's try
02:37:11.200 this out. So let's do we're going to run
02:37:14.560 it again and this time we're going to
02:37:16.720 say what is the capital of USA. Let's go
02:37:19.680 ahead and open this up and we're going
02:37:21.920 to select the before and after tool and
02:37:23.280 we're going to say what is
02:37:25.479 the capital of USA? And now what it'll
02:37:29.600 do is it will return the original result
02:37:32.479 which was just Washington DC but then
02:37:34.720 it's adding that fancy note at the end
02:37:36.240 that we told it to. So you've officially
02:37:38.000 altered the tool response using the
02:37:40.640 after tool call back. Okay, you guys are
02:37:43.439 now officially pros when it comes to all
02:37:46.160 six different types of callbacks that
02:37:48.560 you can use inside your agents. Super
02:37:51.040 excited for you guys to wrap that one up
02:37:53.040 because those are super helpful and
02:37:54.720 you're actually going to see us use the
02:37:56.560 before agent call back. numerous times
02:37:58.560 going forward because it's a super handy
02:38:00.319 one to use. So, now that we've knocked
02:38:02.080 that out of the way, we're going to
02:38:03.280 start diving over to our workflows,
02:38:05.840 which are going to include the
02:38:07.280 sequential, parallel, and loop agents.
02:38:09.520 So, let's hop over to example number 10
02:38:11.439 so we can start working on sequential
02:38:13.040 workflows. Hey guys, and welcome to
02:38:14.880 example number 10, where we're
02:38:16.399 officially starting to work on our first
02:38:18.960 type of workflow agent. And in this
02:38:21.359 example, we're going to focus on the
02:38:23.280 sequential workflow where agents work on
02:38:25.760 a task one after another. So what we're
02:38:28.560 going to do in this example is first hop
02:38:30.399 over to the docs, look exactly at what
02:38:32.240 ADK says about these workflow agents,
02:38:34.479 and then we're going to look at this
02:38:36.640 lead qualification pipeline example that
02:38:39.200 I've created for you guys where we have
02:38:41.040 validator agents that then pass the
02:38:42.960 results to a score agent which then
02:38:44.560 passes the result to a recommendation
02:38:46.000 agent. And then in part two, we're going
02:38:47.840 to look at this code that I've set up
02:38:49.280 for you guys so you can see a working
02:38:50.399 example. And in part three, we're going
02:38:51.680 to run it. So let's hop over to the doc
02:38:53.200 so you can see everything in action. All
02:38:54.960 right, so we're in the sequential agent
02:38:56.640 docs. So let's quickly cover what they
02:38:58.800 are, how they work together, and when we
02:39:00.560 should use them. Okay, so sequential
02:39:02.160 agents, basically it's a type of
02:39:04.080 workflow agent, which means our agents
02:39:06.000 are going to work in a particular
02:39:07.439 pattern. And in our case when working
02:39:09.760 with sequential agents all the sub aents
02:39:12.000 you provide to a rootle agent are going
02:39:14.880 to work in the order that you specify.
02:39:17.439 So the most important thing to note is
02:39:19.520 when you look at the code agents will
02:39:22.000 work in the order that you pass them in
02:39:23.760 in the sub agent list. So if you have
02:39:25.359 agent 1 2 3 it will always run agent
02:39:28.560 123. So execution occurs from first to
02:39:31.439 last. Okay. So here's an example of why
02:39:33.760 you would want to use a sequential
02:39:35.280 agent. Let's imagine you were building
02:39:36.960 an agent that could summarize any web
02:39:38.800 page using two tools. It first wanted to
02:39:41.359 get the page content and then summarize
02:39:42.880 the page. Well, because you can't
02:39:45.359 summarize a page until you have the page
02:39:47.600 content. This would make for a great use
02:39:50.160 case to start using sequential agents
02:39:52.640 where first you would always get the
02:39:54.560 page content and once we've grabbed the
02:39:56.319 page content, we would then go over to
02:39:59.040 option agent number two where you would
02:40:01.040 then summarize it. So that is a
02:40:02.479 sequential agent in a nutshell. So
02:40:05.040 here's just a quick example of what it
02:40:06.880 looks like inside a sequential agent.
02:40:08.720 You'll see that you always provide sub
02:40:10.399 agents where this agent will always be
02:40:12.960 triggered before this agent. And the
02:40:15.120 important thing to note is that you are
02:40:17.120 not, you know, passing state like this
02:40:19.760 arrow does not mean you're passing
02:40:21.200 information from agent A to agent B. You
02:40:23.840 have to use shared state like we've been
02:40:26.160 doing throughout the rest of these
02:40:27.760 examples here together today. So if you
02:40:30.160 wanted agent two to have information
02:40:32.399 that agent one generated, you would need
02:40:34.880 to, you know, write that to state and
02:40:37.280 then sub agent 2 would pull that down.
02:40:39.439 So that's super important to note. So
02:40:41.680 what we can do is we're going to hop
02:40:43.200 over to the code example I've created
02:40:44.560 for you guys, walk through it step by
02:40:46.080 step so you can see how you can create
02:40:48.160 these agents, share state between them,
02:40:50.399 and work together on building, you know,
02:40:52.160 your multi- aent systems that work in a
02:40:53.840 nice workflow. So let's hop over to the
02:40:55.200 code. All right, so let's start to look
02:40:57.120 at how you can start to use sequential
02:40:59.120 agents with inside of ADK. Thankfully,
02:41:01.200 it's a super simple change. So, right
02:41:03.120 now we are inside of the lead
02:41:05.319 qualification folder and we are in the
02:41:07.439 lead qualification agent. And in order
02:41:10.399 to start working with sequential agents,
02:41:12.960 all you need to do is import sequential
02:41:15.520 agent from here. Normally, what you
02:41:17.680 would do is import agent. So, if you
02:41:19.760 look at all of our other multi- aent
02:41:21.880 solutions, every time we're importing
02:41:24.319 our regular agent, but this time instead
02:41:26.399 of importing just a plain old agent,
02:41:28.319 we're saying, "All right, ADK, you are
02:41:30.319 now working with a sequential agent."
02:41:32.479 And inside of a sequential agent, I
02:41:34.399 first want you to, you know, trigger
02:41:36.319 this this sub agent. So, the lead
02:41:38.080 validator agent, the lead score agent,
02:41:40.319 and then the action recommener agent. So
02:41:43.280 in this example, what we're trying to do
02:41:45.040 is create a lead qualification pipeline
02:41:47.680 where I can give some information to
02:41:50.960 this sequential agent and it will save
02:41:53.120 the result for me so I can figure out
02:41:54.560 should I work with this customer or
02:41:56.160 should I not. So what we're going to do
02:41:58.160 is first walk through each one of these
02:42:00.240 agents at a high level so you can see
02:42:01.600 what they do and understand how we're
02:42:03.680 saving the result of each of these
02:42:05.200 agents so that the result from agent one
02:42:08.720 gets passed to agent two and the result
02:42:11.200 from agent two gets passed to agent 3.
02:42:13.280 So let's look at how we can do that. So
02:42:15.439 first things first, we are now looking
02:42:17.280 at the lead validator agent and here's
02:42:20.960 all we have to do. We are going to give
02:42:23.120 this lead validator some instructions
02:42:25.359 saying, "Hey, you're here to validate
02:42:28.240 different clients that I give to you.
02:42:30.080 So, I'm going to give you lead
02:42:31.840 information and what this lead
02:42:34.560 information should include to verify
02:42:36.800 that it's a complete qualification.
02:42:38.800 Basically, to make sure that we're given
02:42:40.000 all the information we need, you're
02:42:41.680 going to get their contact information,
02:42:43.760 what they're interested in, what they
02:42:45.520 need, and some information about the
02:42:47.120 company that they currently work for. If
02:42:49.439 they're if they give us all the
02:42:50.880 information we need as a valid contact,
02:42:53.040 we're going to say valid. Otherwise,
02:42:54.880 you're going to return invalid. That's
02:42:56.880 all you need to do. And what we're going
02:42:58.560 to do is save the result of this entire
02:43:01.840 agent to the output key. So, if you
02:43:04.240 remember from way back when we were
02:43:05.600 working on initially using agents to
02:43:08.000 save the results to state, this is going
02:43:10.800 to save valid or invalid to this key
02:43:14.240 inside of state. So, validation status
02:43:16.240 will either say valid or invalid. Okay,
02:43:18.720 cool. So, now that we've understand what
02:43:20.240 agent one can do, let's go look at the
02:43:22.160 lead score agent, which is going to
02:43:24.000 score the lead that we are given to
02:43:26.319 determine if they're a good fit for us.
02:43:28.160 So, we're going to say, okay, your job
02:43:30.000 is to score. And what you need to do is
02:43:32.880 look at the information that is given to
02:43:34.640 us and score the lead from 1 to 10. And
02:43:37.840 I want you to score based off of how
02:43:40.479 urgent the problem is, if the person is
02:43:42.800 a decision maker, if they have time and
02:43:45.520 budget. From there, what I want you to
02:43:47.120 do is just give me back a numeric score
02:43:50.000 and a one-s sentence justification of
02:43:52.160 why you think we should work with them.
02:43:53.840 So, here's some example outputs. So, we
02:43:56.240 could say eight, which is like, hey,
02:43:57.840 they're a good decision maker, clear
02:43:59.120 budget, the great contact. Or three, we
02:44:01.840 could say, hey, you know, they're not
02:44:03.600 really interested, no timeline, no
02:44:04.880 budget, so they're not a great contact.
02:44:06.800 And once again, we are going to save the
02:44:08.800 output of this to the lead score key so
02:44:12.560 that the result like one of these will
02:44:14.399 be saved to state. Okay, great. So,
02:44:16.319 we're all just building up towards
02:44:17.840 working towards the final step in our
02:44:19.760 sequential workflow, which is all going
02:44:22.000 to be inside the action recommener
02:44:24.240 agent. Now, what this agent is going to
02:44:26.560 do is it is going to take in all the
02:44:29.439 information that we've built so far from
02:44:31.600 our previous steps inside of our
02:44:33.600 sequential workflow. So, we're going to
02:44:35.279 pass in the keys right here. And if you
02:44:37.840 just notice the lead score key, this is
02:44:40.479 exactly what is mentioned here. So lead
02:44:43.439 score key. This is exactly what we have
02:44:46.160 in our recommener. So this is where
02:44:48.160 those keys that we were saving, the key
02:44:49.920 values we were saving to state, this is
02:44:51.680 where we're now getting access to them.
02:44:53.120 So we can start to share state between
02:44:54.640 our agents. And from there, we're going
02:44:56.000 to say, all right, using the information
02:44:57.760 that I've just given you, I want you to
02:45:00.640 create a recommendation on what next
02:45:03.439 steps we should take for this agent. So
02:45:06.560 if the lead score is invalid, just say
02:45:09.680 what additional information we need.
02:45:11.760 then based on the other types of score
02:45:14.240 like if it's a bad score, a good score
02:45:16.160 or a great score suggest what we need to
02:45:18.560 do next. So this is sequential workflow
02:45:21.439 in a nutshell. So what we can do now is
02:45:23.840 we'll hop back to our root agent so we
02:45:26.319 can kick everything off so you can see
02:45:28.399 it all in action. So what we're going to
02:45:30.880 do is we're going to make sure that we
02:45:32.640 are inside of our sequential agent
02:45:34.479 workflow. And I'm going to first open up
02:45:37.359 in the readme I have some examples that
02:45:39.600 you can test here. So we'll first try an
02:45:42.240 unqualified lead. So let's run this. So
02:45:45.040 ADK web and what we'll do is this will
02:45:48.399 trigger our interactive session so we
02:45:50.640 can start chatting with it. So now we
02:45:52.640 can pass in a lead. And if you notice to
02:45:55.120 start there's nothing in state. But if I
02:45:57.279 pass in a lead for John Doe and he's a
02:46:00.640 bad lead, we can watch what happens. So
02:46:03.040 agent one would trigger then agent two
02:46:05.840 would trigger then agent three. So all
02:46:08.399 of these agents right here are getting
02:46:10.720 wrapped up inside of a sequential
02:46:12.240 workflow. So sequential workflow really
02:46:14.160 is nothing more than just a wrapper
02:46:16.080 around all the three agents that you
02:46:18.000 want to do all the work for you. And
02:46:20.240 what you would notice is as we were
02:46:22.399 running the agent in real time, it was
02:46:24.720 saving the results to state. So agent
02:46:27.920 one spit out the if it was valid or not.
02:46:30.479 Agent two, the score was, you know,
02:46:32.720 printing out the quality of the lead and
02:46:34.720 a justification of why they got that low
02:46:36.399 score. And then the final agent, our
02:46:38.720 third agent was saying, "Hey, based on
02:46:41.120 the two previous pieces of information,
02:46:43.520 I recommend that John Doe is not a good
02:46:46.160 client for us to work with. I recommend
02:46:48.240 just continue doing some education to
02:46:50.399 see if he better understands what's
02:46:51.840 going on and if we can work with him."
02:46:53.359 So, that's option one. But what we could
02:46:55.279 do is let us hop back over to our
02:46:58.720 examples that we have set up. And in
02:47:01.120 this time, we're going to pass in a
02:47:02.960 qualified lead. So, let's scroll back up
02:47:05.520 to where things got kicked off a second
02:47:07.279 ago. And now we can do another message
02:47:10.640 and this time do it for a great client.
02:47:12.640 So, Sarah is a great client, great
02:47:14.880 budget, leadership position, all around
02:47:17.200 great spot. So, you can see that's
02:47:18.880 exactly what the agent said, too. This
02:47:20.560 is the valid lead. This is a high score.
02:47:22.720 She's a CTO. She's trying to, you know,
02:47:25.439 she has a budget and a timeline. And the
02:47:27.439 recommendation is that Sarah's trying to
02:47:29.439 switch away from a competitor. What I
02:47:31.439 recommend to do is schedule a demo with
02:47:33.279 her and prepare a proposal. Yeah, you
02:47:34.960 can see it did exactly what it was
02:47:36.319 supposed to do and it saved everything
02:47:38.240 to state and that's how it was able to
02:47:39.840 come up with this awesome response right
02:47:41.359 here. So yeah, that was sequential
02:47:43.040 workflows in a nutshell. Hopefully that
02:47:45.680 made sense because if you're familiar
02:47:47.600 with working with tools like Crew AI,
02:47:50.560 this is probably more of what you're
02:47:52.399 used to to where you have different
02:47:54.399 agents all working on one task. So
02:47:57.120 definitely sequential workflows are
02:47:58.800 amazing and we're now going to move on
02:48:01.200 to the next example where you're going
02:48:03.279 to start to see how we can actually
02:48:04.640 trigger multiple agents to go work in
02:48:07.200 parallel and then combine the answers.
02:48:08.640 So let's hop over to example number 11.
02:48:10.640 All right, welcome to example number 11
02:48:12.960 where you're going to start to work with
02:48:14.640 parallel agents. Now in this example,
02:48:16.960 we're first going to head over to the
02:48:18.640 Google doc so you can see why they
02:48:20.399 recommend to use these agents, when to
02:48:22.319 use them. From there, I have a pretty
02:48:24.240 cool code example where we're going to
02:48:26.000 monitor all of our computer analytics
02:48:28.399 and, you know, use parallel agents to
02:48:30.160 quickly go off and find all the
02:48:31.920 information about our computer and give
02:48:33.200 us a nice little report. And then in the
02:48:35.520 third example, we're going to run this
02:48:37.359 code that I've created for you guys. So,
02:48:38.800 let's hop over to the docs so you can
02:48:40.720 see all the core information you need to
02:48:42.399 know. Okay, so let's dive into what are
02:48:44.399 parallel agents, when you should use
02:48:46.160 them, and then a quick example of how
02:48:48.080 they all work. So first things first, a
02:48:49.840 parallel agent, it's another type of
02:48:51.359 workflow agent where we are structuring
02:48:53.439 our agents in a particular format to go
02:48:55.760 off and do work. Now in the the case of
02:48:58.000 parallel agents, instead of agents, you
02:49:00.080 know, being triggered one after another,
02:49:02.800 which is usually slow because you have
02:49:04.240 to wait for agent one to finish, then
02:49:05.520 agent two, then agent three. Well, with
02:49:07.680 parallel agents, what we're doing
02:49:09.200 instead is we are going to do things in
02:49:11.760 parallel. So where all of our agents are
02:49:14.000 going to generate and do work all in
02:49:16.560 parallel, so it's much faster. And then
02:49:18.720 afterwards once all the work's done is
02:49:20.800 we can use all the information that they
02:49:23.040 saved to state and then in the final
02:49:25.359 agent take all that raw information and
02:49:27.600 spit out a nice report. That's the usual
02:49:29.600 type of workflow for a parallel agent.
02:49:31.840 So whenever you want to focus on speed,
02:49:34.399 this is the agent workflow for you,
02:49:36.560 especially when you need a lot of work
02:49:37.840 to get done. So let's look at a few
02:49:41.040 quick examples of what they recommend.
02:49:43.520 So in this case, if you wanted to do a
02:49:45.680 parallel agent that you know, let's
02:49:48.000 imagine you just wanted to do a lot of
02:49:49.520 work. Most basic example is just agent
02:49:51.439 one does work, agent two does work,
02:49:53.040 agent three does work, and they all
02:49:54.640 create outputs. Now, this is handy and
02:49:56.880 helpful cuz you're going to get a lot
02:49:57.920 done really quickly. But like I
02:49:59.520 mentioned earlier, most of the time you
02:50:01.279 want to combine all of these results
02:50:03.359 into something that the final agent can
02:50:05.920 look at and generate a super nice report
02:50:08.080 that you can start to look at. That's
02:50:09.520 usually what you want to do with
02:50:10.319 parallel workflows. So now you've seen a
02:50:12.479 high-level overview of what the agents
02:50:14.720 look like. Let's hop over to the code
02:50:16.160 example where this will make so much
02:50:17.600 sense cuz it's actually super easy to
02:50:19.279 use. So let's hop over to the code so
02:50:20.560 you can see all this in action. Okay, so
02:50:22.240 it's now officially time for us to get
02:50:23.760 our hands dirty working with parallel
02:50:25.680 agents. Now in this example, we're
02:50:28.000 actually using sequential agents and
02:50:29.680 parallel agents. So don't let it confuse
02:50:31.359 you, but I'm going to walk you through
02:50:32.640 everything step by step. Okay, so first
02:50:35.520 off, what we need to do is look at our
02:50:38.399 root agent. And what I want to call out
02:50:40.640 is our root agent has two sub agents. So
02:50:43.600 what's happening is the first agent is a
02:50:46.479 parallel agent. This parallel agent, we
02:50:49.040 import it just like we do with
02:50:50.479 everything else. Parallel agents up
02:50:52.080 here, sequential agents, regular agents,
02:50:53.600 we all import it from the same place.
02:50:55.200 Now, but here's what's happening under
02:50:56.640 the hood. We are generating multiple
02:50:59.600 agents to go off and do work. So the
02:51:01.439 first agent is going to be the CPU
02:51:02.960 agent. So it's going to do work. We have
02:51:05.120 a memory agent which goes off and looks
02:51:06.640 at how much memory we have available on
02:51:07.920 our computer. And the final agent looks
02:51:09.680 up how much hard drive space we have on
02:51:11.439 our computer. And all of these agents
02:51:13.600 are going to get wrapped in a sequential
02:51:15.840 workflow. That's exactly what the system
02:51:18.479 information gatherer parallel agent is
02:51:20.640 doing. So when you see this right here
02:51:22.960 in your head, you should be thinking,
02:51:24.399 okay, I have three agents running in
02:51:26.560 parallel and they're just wrapped in one
02:51:28.800 parallel agent. Great. Now going back to
02:51:32.080 our sequential agent, you can see the
02:51:34.319 second item that we have is a system
02:51:37.120 report synthesizer. So what this is
02:51:39.040 going to do is it's going to take all
02:51:40.560 the information that these agents are
02:51:43.040 saving to state. So they're all saving
02:51:44.800 to state and this system report
02:51:47.200 generator is going to then say great I
02:51:49.279 understand everything that you've done.
02:51:50.640 I'm going to put it in nice report. So
02:51:52.080 the like final result is you're going to
02:51:53.760 have just a quick repeat is you're going
02:51:55.439 to have parallel workflow that's going
02:51:57.279 to have three agents and then you're
02:51:58.960 going to have one final agent that's
02:52:01.120 going to work and all of this is going
02:52:02.960 to live inside of this sequential agent
02:52:05.520 right here. So sequential agent is
02:52:07.359 running the parallel agent first and
02:52:09.439 it's going to pass their final results
02:52:10.800 over to the system report synthesizer.
02:52:12.560 So hopefully that makes sense and
02:52:13.680 hopefully you're starting to see like oh
02:52:14.720 wow I can start to chain together
02:52:16.640 parallel agents within sequential
02:52:18.160 agents. Like the world is your oyster.
02:52:19.600 You can do whatever you want. So, what
02:52:20.880 I'd like to do is first walk through
02:52:22.640 what each one of these agents does at a
02:52:24.399 high level because I think it's pretty
02:52:25.680 cool. And then you'll see how we start
02:52:27.760 to save each one of the results from
02:52:29.120 these to state and then access all the
02:52:31.439 saved information and make a nice
02:52:32.880 report. So, let's dive into the CPU
02:52:34.319 agent first. And when it comes to best
02:52:36.640 practices, what you'll start to know as
02:52:38.399 you build larger and larger agent
02:52:40.160 workflows is within each agent to keep
02:52:43.920 things nice and tidy, you'll first want
02:52:45.840 to create your agent.py. And then if
02:52:47.840 there's any particular tools that you
02:52:49.920 want this agent to use, you usually
02:52:51.439 break them out into tools.py file to
02:52:53.359 where eventually each folder is going to
02:52:55.520 have its own agent.py and its own
02:52:57.359 tools.py. So it just keeps things very
02:52:59.120 very clean and it keeps your files very
02:53:01.279 lightweight. So let's dive into looking
02:53:03.439 at the CPU agent where basically what
02:53:05.920 it's going to do is all it really is
02:53:08.160 going to do is call the get CPU data
02:53:11.520 function and this is going to call the
02:53:14.040 psutils library. So, this is a library
02:53:16.640 that we've already installed and what
02:53:18.560 it's going to do is it's going to see
02:53:19.840 how many CPUs you have and it's going to
02:53:22.240 put all this in a nice dictionary that
02:53:24.640 we can return to our agent. So, you can
02:53:26.960 see this this is a huge bit of
02:53:29.120 information we're going to return. So,
02:53:30.160 we're going to turn the CPU stats, we're
02:53:31.920 going to return all the cores, we're
02:53:34.000 going to return all sorts of information
02:53:35.600 back to our agent. And the most
02:53:37.200 important thing is let's get out of
02:53:38.720 tools. All of that information that we
02:53:40.319 get from our tool call is going to get
02:53:41.840 saved to CPU information. Great. So now
02:53:44.880 let's go look at our next agent which is
02:53:46.399 going to be the memory info agent. Now
02:53:48.800 our memory info agent once again is
02:53:51.120 going to have instructions for like hey
02:53:52.640 your job is to go get anything related
02:53:54.640 to memory when it comes to the computer
02:53:56.800 and you're going to report back usage if
02:53:58.560 you know if they're using a ton of
02:53:59.760 memory. And in our case we're going to
02:54:01.760 have another tool once again going to
02:54:03.680 use the psutil library. And we're just
02:54:06.160 trying to put as much information in
02:54:08.240 this tool call as we possibly can and
02:54:10.720 return it in a dictionary because that's
02:54:12.479 what ADK likes. It wants our tools to
02:54:14.720 return dictionaries with as much
02:54:16.240 information as we possibly can for the
02:54:18.240 agent to easily read through it. Per
02:54:20.160 usual, we're going to save the results
02:54:21.520 to an output key so that it gets saved
02:54:23.600 to state. And then finally, what we're
02:54:25.439 going to do is go over to our disk
02:54:27.040 information agent. And what we're going
02:54:28.640 to do with our disk information agent,
02:54:30.080 pretty much same thing that you've seen
02:54:31.120 for everything else. We're going to look
02:54:32.640 at what we have saved to our disk. If we
02:54:35.359 have too much information saved to our
02:54:36.880 disc, we're going to say, "Hey, it's
02:54:38.160 high usage." Then finally, we're once
02:54:40.640 again calling the PS utils library where
02:54:43.200 we're going to check and basically make
02:54:44.800 a few requests to see what disk we have
02:54:46.560 available and how much we are using for
02:54:49.279 each device we have on our computer. So
02:54:51.200 all in all, pretty cool code and we're
02:54:53.120 going to return all the information. So
02:54:54.880 that's everything at a high level for
02:54:57.120 all of our parallel agents that are
02:54:59.040 going to go work separately because
02:55:00.640 there's no reason there's no reason for
02:55:02.880 us to do agent one then wait a few
02:55:05.200 minutes or a few seconds then call agent
02:55:07.040 two then call agent three afterwards
02:55:09.359 like all of these can be done in
02:55:11.040 parallel to save time. So that's why
02:55:13.520 we're doing this. And then finally, once
02:55:15.760 all of these agents have gone off and
02:55:17.520 saved everything to state, we're then
02:55:19.520 going to use the system report
02:55:21.120 synthesizer to access all that saved
02:55:23.200 information and make a nice report. So
02:55:25.120 this is where you can start to see how
02:55:26.560 everything comes together. So you can
02:55:28.319 say, great, you are here to generate a
02:55:30.319 nice report on my system. Here's all the
02:55:32.800 raw information you need to know. You
02:55:34.960 have access to CPU information that's
02:55:36.800 saved to state. You have access to
02:55:38.560 memory and disk information that are
02:55:40.479 also saved to state. and I want you to
02:55:42.560 make a well formatted report is
02:55:45.120 basically in markdown that you can then
02:55:47.200 show to me. So that's exactly what we're
02:55:48.800 doing. So let's run this bad boy so you
02:55:51.359 guys can see it in action. So we need to
02:55:53.279 go over to our example number 11 for
02:55:55.760 parallel agents. And now we can run ADK
02:55:58.160 web. When we run ADK web, it's going to
02:56:01.120 kick off our server. And you can see it
02:56:04.560 already shows us the root agent. And
02:56:06.560 just a quick reminder that root agent
02:56:08.319 has a parallel workflow for the first
02:56:10.640 agent and then the second agent is going
02:56:12.800 to be that system report. This is all
02:56:14.640 handled under our a sequential agent
02:56:17.520 that has a parallel agent and a regular
02:56:19.040 one. Okay, great. So what we can say is
02:56:21.120 say please get the stats for my
02:56:24.160 computer. Now what this will do is it
02:56:26.319 will trigger all sorts of states. So we
02:56:28.240 should start to see each one of these
02:56:29.680 get triggered in parallel. I mean that
02:56:31.040 happens so fast it's it's it's hard to
02:56:32.479 keep up. See that's the power of
02:56:33.520 parallel. But you can see at the same
02:56:35.600 time we made requests to each tool where
02:56:39.600 normally if we were to not use parallel
02:56:41.840 workflows it would have been okay step
02:56:43.600 one call get CPU great I got the answer
02:56:47.120 now I'll move on to the next one great I
02:56:49.359 got the answer cool now I'll go to the
02:56:51.520 third one got the answer so as you can
02:56:53.439 see this was so much faster from there
02:56:55.760 in real time we were getting back all of
02:56:58.080 the information in a nice little report
02:57:00.240 so each agent was spitting out the
02:57:02.160 results so you can see when I click
02:57:03.760 Click on this agent. You can see the
02:57:05.439 memory. Oh, this is pretty cool. I'll
02:57:07.120 I'll zoom out so you guys can see it.
02:57:08.560 So, you can see in our parallel
02:57:09.920 workflow, we have access to three
02:57:12.000 different agents. And you can see when I
02:57:13.920 click on each agent, like it just so
02:57:15.680 happened that agent two finished before
02:57:17.600 agent one because in in parallel
02:57:19.680 workflows, order is not guaranteed and
02:57:21.600 it doesn't matter because it's all
02:57:22.720 happening in parallel. But you can see
02:57:24.399 this agent was able to report back how
02:57:26.160 much memory I have available, usage, and
02:57:28.080 so forth. The next I can see my CPU
02:57:30.240 agent said, "Hey, your system has 10
02:57:32.319 cores. you're using not a ton. Great.
02:57:34.800 And then finally for my disc agent, you
02:57:36.960 can see I have like external hard drives
02:57:38.720 and everything hooked up. So everything
02:57:40.000 looks good. And then finally, when it
02:57:42.000 comes to the final report, you can see
02:57:44.240 uh cuz these were all wrapped in a
02:57:45.920 sequential workflow. So this one was
02:57:47.760 step one and this one was step two. So
02:57:50.000 you can see step two looked at all of
02:57:52.399 the state information. So I can actually
02:57:54.720 scoot over here. So you can see in
02:57:56.720 example number two, it was given access
02:57:58.960 to I can actually go in here and show
02:58:00.880 you guys. Yeah. So your job is to be a
02:58:03.920 system report information. And then
02:58:06.080 right here for CPU information, we
02:58:08.240 actually passed in all the information
02:58:10.479 from report number one. And then when it
02:58:12.479 comes to memory information, we passed
02:58:14.800 in everything from report number two. So
02:58:16.399 all this got passed in a prompt and then
02:58:18.319 it generated this super nice looking
02:58:19.920 report for us. So we can get a good
02:58:21.680 understanding of what's going on in our
02:58:23.439 computer and if we need to do anything
02:58:25.359 else. And overall, thank god my
02:58:26.800 computer's in good condition. I'd be
02:58:28.319 hosed if it wasn't. I wouldn't be upset
02:58:30.000 if I got a new computer, though. And uh
02:58:31.920 yeah, you can see everything is looking
02:58:33.439 great. So this is parallel agents in
02:58:36.319 action. And just quick reminder, you
02:58:38.640 want to use parallel agents whenever you
02:58:40.880 want to do a lot of work at the same
02:58:42.960 time. All right, great. So now we are
02:58:45.200 almost done, guys. We can now go to our
02:58:47.439 final example, which is loop agents,
02:58:49.920 which is going to be one of the most
02:58:51.359 powerful workflow tools available inside
02:58:53.680 ADK. So let's hop over to our final
02:58:55.439 example, example number 12. All right,
02:58:57.359 give yourself a pat on the back cuz
02:58:58.960 you've officially made it to the final
02:59:00.720 example inside this ADK crash course.
02:59:03.600 And in example number 12, we're going to
02:59:05.840 focus on adding in loop agents workflows
02:59:09.760 to our toolkit. Now, what we're going to
02:59:11.680 focus on in this one is you're going to
02:59:13.600 see how you can begin to use loop agents
02:59:15.760 to have your agents iterate on a problem
02:59:17.920 over and over and over again to solve a
02:59:19.840 specific problem until they get an
02:59:21.600 answer. This is one of the most powerful
02:59:23.200 features in my opinion and it feels a
02:59:25.600 lot like how crew AI in lane chain will
02:59:28.240 use agents in the react format which
02:59:30.880 stands for reason and act where agents
02:59:32.960 will continually think about a problem
02:59:34.479 and work on it over and over and over
02:59:36.240 again until they get an answer. So this
02:59:37.840 is a super powerful pattern and in this
02:59:40.479 example breakdown we're first going to
02:59:41.840 head over to the docs look at what ADK
02:59:44.000 recommends then we're going to dive into
02:59:45.439 the code and then we're going to run
02:59:46.479 this bad boy. So let's hop over to the
02:59:48.080 code so you can see everything you need
02:59:49.600 to know. Okay, so when it comes to loop
02:59:52.000 agents, the main thing you need to know
02:59:54.479 is loop agents are basically sequential
02:59:57.120 agents but on steroids. And what I mean
02:59:59.439 by that is loop agents will continually
03:00:02.160 run until we've run out of iterations.
03:00:05.200 So like, hey, only try to solve this
03:00:07.359 problem five times. So it'll run
03:00:09.120 multiple times or until a specific
03:00:11.840 condition is met. So we can say, "Hey,
03:00:13.680 please continue to search the internet
03:00:15.200 until you find five resources that I can
03:00:18.399 use for my report." So that's
03:00:20.560 continually solving the problem over and
03:00:22.399 over and over again until we meet one of
03:00:24.399 these criteria. A max iterations or
03:00:26.720 until we meet a specific condition that
03:00:28.319 we specify. So here's a quick example of
03:00:30.720 what ADK recommends. So let's say you
03:00:33.520 want to build an agent that can generate
03:00:35.040 images of food, but sometimes when you
03:00:36.880 generate a specific number of items,
03:00:38.160 like five banana, it generates a
03:00:39.920 different number of those items in the
03:00:41.279 image. So because you have two tools in
03:00:44.160 your agent, you know, option one could
03:00:46.800 generate the image and then option or
03:00:48.800 sorry agent two could count the food and
03:00:50.800 basically you would have those agents
03:00:52.560 continue to go and work over and over
03:00:55.359 and over again until it generated an
03:00:58.399 image that you know had the right
03:01:00.000 quantity. So that's exactly what you
03:01:01.760 would want to do when working with loop
03:01:03.680 agents. And they're actually super super
03:01:05.760 easy to use, but there is a little bit
03:01:07.840 of trickiness when it comes to exiting a
03:01:10.880 loop. So that's exactly what we're going
03:01:12.399 to cover now in the code. So you can see
03:01:14.240 all this in action. So let's hop over to
03:01:15.840 the code. Okay. So it's now time to look
03:01:18.080 at our final code. So in this example,
03:01:20.960 we are focusing on creating a loop
03:01:23.520 agent. And if you remember the core
03:01:25.760 things to know about loop agents is that
03:01:28.319 they exit when one of two things
03:01:30.560 happens. First, whenever we hit max
03:01:33.279 iterations or whenever we meet a certain
03:01:36.479 condition that says we're good, we're
03:01:38.880 done. We don't want to work anymore. And
03:01:40.560 now it's time to quit. And you'll see
03:01:42.319 how we can do that in just a second
03:01:44.399 inside of our sub agents. And the other
03:01:46.720 thing, the core reminder to note is in
03:01:49.279 our sub agents, what happens is we
03:01:51.600 always first do this one. We always do
03:01:54.560 the first one first and then we always
03:01:56.080 go to the second and we just continue
03:01:57.680 the cycle over and over and over and
03:01:59.040 over again. So what we're also going to
03:02:01.600 do is inside of this agent is we
03:02:04.399 actually have two parts to it. So part
03:02:06.640 one is we are going to create an initial
03:02:09.120 LinkedIn post and then part two is going
03:02:11.520 to be the loop where the loop is exactly
03:02:13.600 what you just saw where we have one
03:02:15.600 agent that reviews it and then we have
03:02:17.200 one agent that actually implements the
03:02:19.279 changes. So that's exactly what we have
03:02:21.200 going on in here. So if we were to draw
03:02:23.680 this out, step one is generate post and
03:02:26.800 then step two is we have our loop agents
03:02:29.760 where our first agent is going to review
03:02:32.080 and the next one's going to refine and
03:02:34.319 it's just going to go in a workflow just
03:02:36.640 like this over and over and over again
03:02:39.279 until we get that beautiful LinkedIn
03:02:40.880 post. So let's start to look at each one
03:02:43.359 of these step by step so you can see how
03:02:45.120 state is shared amongst all of these
03:02:47.200 different agents from our sequential
03:02:49.040 agents all the way to our loop agents.
03:02:51.600 So let's hop into our initial post
03:02:53.040 generator so you can see exactly what
03:02:55.279 it's doing. So in this case we're saying
03:02:57.120 all right you are a LinkedIn post
03:02:59.520 generator and what I would like you to
03:03:01.840 do is to create a LinkedIn post about
03:03:04.880 agent development kit uh from the
03:03:06.880 tutorial that I'm creating for you guys.
03:03:08.399 So this is uh hey if you want to take a
03:03:10.399 moment to share the post that we're
03:03:11.840 going to create mean the world to me and
03:03:13.520 also like and subscribe all the
03:03:15.040 goodness. And here are the requirements
03:03:17.600 for this post. You need to talk about
03:03:19.680 how you are excited. here's everything
03:03:21.520 that we covered in this tutorial so that
03:03:23.600 there are, you know, the agent knows
03:03:24.960 exactly what we've worked on together.
03:03:26.640 We're also saying here's the style
03:03:28.399 requirements, no emojis, no hashtags.
03:03:30.960 And then finally, what I want you to do
03:03:32.880 is only return the post. Don't do any
03:03:35.520 additional commentary, and don't do any
03:03:37.520 formatting markers. Just give me the
03:03:39.040 post, nothing else. And per usual,
03:03:40.960 because we want to save the output of
03:03:43.279 this agent to state so that the next
03:03:45.520 agents can use it. And that's where
03:03:47.120 we're going to use our output key once
03:03:48.800 again to save it to state under current
03:03:50.800 post. Great. So now let's look at uh the
03:03:53.760 agents with inside of our loop agent. So
03:03:56.720 our loop agent, the first one that we
03:03:58.160 always are going to do and trigger is
03:03:59.920 going to be the post reviewer. So the
03:04:02.240 post reviewer, let's walk through these
03:04:04.479 instructions carefully. First things
03:04:06.399 first, we specified that the post we're
03:04:09.920 generating needs to be within a,00 to
03:04:12.720 1500 characters. So you need to use the
03:04:15.279 character count tool to make sure and
03:04:17.439 check the post length. If it's too big,
03:04:19.439 too small, we need to do another
03:04:20.720 iteration. So this is where we're just
03:04:22.479 giving instructions on what to do if the
03:04:24.479 length is too big or too small. From
03:04:26.560 there, if the length is correct, we then
03:04:29.120 want to make sure that our post meets
03:04:31.040 all of these criteria. So you want to
03:04:33.040 say it mentions my name, it has a clear
03:04:34.960 call to action, shows genuine
03:04:36.640 excitement, and once again, we want to
03:04:38.880 make sure that all of these different
03:04:40.960 style requirements are met. If any of
03:04:42.960 them don't pass, we need to say, "Hey,
03:04:45.040 something went wrong." And if something
03:04:46.640 does go wrong for any specific reason,
03:04:48.960 you need to return a concise
03:04:51.120 instructions on what went wrong. And
03:04:53.279 then for whatever reason, if all of the
03:04:55.760 requirements are met, if things go well,
03:04:58.479 I want you to call the exit loop
03:05:00.319 function. And this exit loop function is
03:05:02.960 the special case where we can actually
03:05:05.600 have our agent break out of the loop.
03:05:07.680 So, what I want to do first is look at
03:05:10.080 how we're going to count characters.
03:05:12.160 Then we're going to look at the exit
03:05:13.680 loop so you can see how you can actually
03:05:15.200 have your agents quit the loop. And then
03:05:17.040 the only other thing I was going to
03:05:18.000 mention is obviously in order for us to
03:05:20.000 review the agent, we need to access our
03:05:22.240 current post in state. Okay, so let's go
03:05:24.560 look at our character count tool first.
03:05:26.960 And as I mentioned a while ago, as you
03:05:29.279 begin to build bigger and bigger agents,
03:05:31.279 you want to start to save your tools
03:05:33.680 next to your agents in one nice tidy
03:05:36.000 folder. So let's look at this. So in
03:05:37.840 this case, we're saying, all right, when
03:05:39.439 it comes to the count character tool, I
03:05:41.840 want you to give me the text and I want
03:05:44.240 the tool context. When it comes to, you
03:05:47.120 know, looking at if the post is too big,
03:05:50.399 we're first just going to call length.
03:05:53.680 This is a built-in Python function, and
03:05:55.600 we're going to look at the length of the
03:05:56.880 entire post. If the length is too short,
03:06:00.479 we're going to return a result saying,
03:06:02.160 "Hey, I sorry, we're going to say I
03:06:05.040 failed." And the reason why is because
03:06:07.120 my character count is too tiny. Here's
03:06:09.359 the current one. I need you add in an
03:06:11.600 additional 20 characters. And then we're
03:06:13.359 going to have a nice little message that
03:06:14.800 puts it all together where it says,
03:06:16.240 "Hey, post is too short. Add this many
03:06:18.160 characters. The minimum length is this."
03:06:19.920 So, we're just reminding the agent what
03:06:21.600 it needs to do. If it was too big, what
03:06:24.160 we're going to do is say, "Hey, you
03:06:26.080 know, you need to the post is too long.
03:06:28.399 Remove this many characters. Here's the
03:06:30.000 max length." So, that's all this tool
03:06:32.319 does. And outside of that, we're just
03:06:34.080 updating the review status to fail if
03:06:36.640 any of these requirements aren't
03:06:38.080 validated. Finally, if the post is not
03:06:40.399 too big or too small, we're going to say
03:06:42.479 everything was a pass. And we're going
03:06:44.080 to have this tool return a a message
03:06:46.800 that says, "Yep, everything passed.
03:06:48.560 Here's the character count, and
03:06:50.160 everything looked great." So that's what
03:06:52.240 the character count tool is going to do.
03:06:55.040 Now, we get to dive into the exit loop
03:06:57.359 functionality. And this is where you are
03:07:00.000 going to have your agents say, "Life's
03:07:02.399 good. I'm happy with the result." Quit
03:07:04.720 iterating and going over and over in the
03:07:06.560 loop. So this is exactly what you need
03:07:08.399 to do. All you have to do is accessing
03:07:11.200 the tool context that you can pass into
03:07:14.000 your tool calls. You are going to say
03:07:16.160 tool context actions escalate. And
03:07:18.960 escalate, all it does is it exits the
03:07:20.880 current loop. Super simple to use. And
03:07:22.960 then you just return none. That's all
03:07:24.800 you got to do. All right, great. So now
03:07:26.880 that you've seen how we can review a
03:07:28.319 post, let's look at what happens if
03:07:30.399 there is feedback. So we're now going to
03:07:32.319 go over to the post refiner agent who's
03:07:34.640 responsible for taking in the input and
03:07:37.040 acting on it. So we're going to say, all
03:07:39.279 right, you are the LinkedIn post
03:07:41.359 refiner. Your job is to refine the
03:07:43.520 LinkedIn post based on feedback I give
03:07:45.600 you. Here's the current post saved to
03:07:48.240 state. And what I want you to do is look
03:07:50.399 at the feedback that I've given you from
03:07:53.359 the previous agent. Because if you
03:07:55.200 remember everything's getting saved to
03:07:57.040 review feedback. So that's what we're
03:07:58.640 accessing right here. Now what we're
03:08:00.240 saying when it comes to the actual task
03:08:01.760 for this you know hey please apply the
03:08:04.640 feedback appropriately to improve the
03:08:06.319 post. You know don't get wild don't
03:08:08.399 change everything. Keep it as you know
03:08:10.000 similar as possible. Here's the
03:08:11.760 requirements one more time as you're
03:08:13.279 making the feedback changes and then go
03:08:15.520 from there. And the job is once it's
03:08:17.840 done. So here's like where the loop
03:08:19.279 happens. It's going to save the changes
03:08:21.439 it makes to current post. So what's
03:08:23.760 happening is like first what's happening
03:08:25.600 is like we generate the post from there
03:08:28.160 we are reviewing the post and then
03:08:30.000 refining it and then I don't know why
03:08:31.920 it's dropping away like that but once we
03:08:34.160 refine the post we're saving the results
03:08:36.319 back to current post so that when we go
03:08:38.560 to review it again we know exactly where
03:08:40.640 to look. Okay great hopefully this makes
03:08:42.560 sense. So now that we've seen it all in
03:08:44.800 the instructions let's run this bad boy
03:08:46.640 so you can see it in action. So let's
03:08:48.800 clear everything out. We're going to
03:08:50.720 make sure we change directories over to
03:08:53.040 the proper folder. So you need to be in
03:08:55.600 the final example and you need to make
03:08:57.359 sure our environment is activated. And
03:08:59.520 now we can run it. So we can just type
03:09:00.800 in adk web and this will generate a post
03:09:04.319 for us or sorry this will open up the
03:09:05.760 browser so that we can generate a post.
03:09:08.160 So I'm going to say please generate a
03:09:11.120 post saying that this was the best ADK
03:09:16.080 tutorial I've ever watched.
03:09:19.760 Now, what this is going to do, let's
03:09:21.120 make this a little bit bigger for you
03:09:22.160 guys. Now, we're going to generate this.
03:09:25.200 From there, what we would expect to see
03:09:26.720 is our initial
03:09:28.600 postgenerator agent go off and run. And
03:09:31.680 this is where it will make a initial
03:09:33.439 rough draft of saying, "Hey, AI with
03:09:35.520 Brandon did an awesome job. I learned a
03:09:38.080 ton." But you can see I'm going to let
03:09:40.319 it run cuz it's it's doing its loop
03:09:41.760 thing. Yeah. Okay. So, now we can start
03:09:43.439 to look at it. So, you can see it took
03:09:45.439 its first attempt. It did a pretty good
03:09:47.439 job. like this is a really nice looking
03:09:49.200 rough draft. Then we had our second
03:09:52.080 agent start to go through and count
03:09:55.040 characters. So you can see at this point
03:09:57.040 what's happening is we're at this step.
03:09:59.439 So the initial post generator sorry yeah
03:10:01.439 the initial post generator already ran
03:10:03.439 right here and now we are already in
03:10:06.240 post refinement specifically we are
03:10:08.560 looking at the post reviewer and the
03:10:10.000 post reviewer always counts characters
03:10:12.800 and we can see oh it looks like this
03:10:14.479 post is too short. you need to add more
03:10:16.640 details to meet the minimum length. From
03:10:19.439 there, the refiner agent takes in all
03:10:22.240 the information and generates a much
03:10:24.240 longer post. Except this time, it went
03:10:27.040 way too hard. So, you can now see in the
03:10:28.960 count character tool, you know, hey,
03:10:30.720 this post is way too long. You need to
03:10:32.560 remove like almost half the characters.
03:10:34.640 This is crazy. So, then it does it again
03:10:37.040 where this time it does a pretty much a
03:10:39.200 lot better job. And this time, you can
03:10:41.760 see it counted the characters. Things
03:10:43.680 are looking great. Now we are in a state
03:10:47.279 to where this post now basically this
03:10:50.960 post reviewer so this is the output from
03:10:52.640 post reviewer it says this post mentions
03:10:54.560 Brandon it talks about everything it
03:10:56.240 needed to and then because everything
03:10:58.240 looked good we can now exit the loop so
03:11:01.120 we should be able to see our final state
03:11:03.920 in here so if we go to state this is the
03:11:07.120 final output of our agent where this
03:11:10.479 post has all the core requirements where
03:11:12.640 it's not too long it's not too short and
03:11:15.359 everything looks great. So you can see,
03:11:17.439 yep, this is so excited. It talks about
03:11:19.680 everything, you know, I've been
03:11:21.200 brainstorming. Yeah, everything about
03:11:22.399 this post is just like what you would
03:11:24.160 need to do because it meets all our
03:11:25.200 criteria. So yeah, that is our loop
03:11:28.080 agents in a nutshell. And just a core
03:11:30.479 quick core reminder, the way it worked.
03:11:32.960 So you remember the core lessons is loop
03:11:35.200 agents will continually work until one
03:11:37.600 of two things happens. First, it will
03:11:40.160 exit if we iterate too many times and
03:11:41.920 it'll say, "Hey, I was unable to get you
03:11:43.600 the answer you wanted." Or option two is
03:11:46.720 when the agent it does everything it was
03:11:48.880 supposed to and we call exit loop where
03:11:51.439 all we do is escalate to say escalate
03:11:53.760 true and we'll break out of the loop.
03:11:55.520 But yeah, you guys are now officially
03:11:57.359 experts at working with all sorts of the
03:11:59.840 different workflows and everything else
03:12:01.200 when it comes to creating ADK agents.
03:12:03.760 And just a few quick reminders, you can
03:12:05.439 download all the source code that you
03:12:06.880 saw today completely for free. Just
03:12:08.720 click the link down the description
03:12:09.840 below. Also, if you have any questions,
03:12:12.080 you can either drop a comment down
03:12:13.439 below, or you can head over to the free
03:12:15.600 school community I created for AI
03:12:17.279 developers just like you, where you can
03:12:18.960 hop on our weekly free coaching calls
03:12:20.720 and get direct feedback from me so we
03:12:22.720 can get you unstuck and moving forward.
03:12:24.479 But that's for this video, guys, today.
03:12:26.160 And I have a ton of other AI related
03:12:28.479 content on this channel and a bunch more
03:12:30.399 tutorials coming out for more ADK
03:12:32.319 content. Definitely recommend checking
03:12:34.000 out all the other videos I have and
03:12:35.520 whichever videos are popping up right
03:12:36.960 now on the screen. But until the next
03:12:38.319 one, can't wait to see you guys. Have a
03:12:39.680 good one. Bye.
