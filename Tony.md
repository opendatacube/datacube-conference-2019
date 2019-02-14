# Hello From Tony

## Looking Forward to Enhancment Proposal wiki

I will fill out the template once it is created for ODC-lite


## OSIP 123 - Implement a simple ODC-lite introduction

### Overview
Proposed By

Andrea Aime
Assigned to Release

This proposal is for GeoServer 2.15-beta.
State

    Under Discussion
    In Progress
    Completed
    Rejected
    Deferred

Motivation

GeoServer currently automatically publishes layers on all suitable services. In order to selectively publish a layer onto specific services, one has to resort to either GeoFence or a custom security manager.

However, deciding a layer service availability is not always a security matter, in those cases setting up a security system just for that is overly complicated. It would be easier to have this configuration directly in the layer "publishing" tab instead.
Proposal

UI wise, we are going to add a service selection configuration in the publishing tab of layers:

Service layer settings

Configuration wise, this is going to be backed by two new properties in the ResourceInfo:

    serviceConfiguration, boolean
    disabledServices, List<String>

The first one controls if the service configuration is enabled, and defaults to false, thus defaulting to showing the layer on all services, while the list of disabled services provides the basis for service filter (more on these choices in the backwards compatibility section).

The user interface should only show services meaningful for a given layer, for example, it should avoid listing WCS for vector layers. Other services, like GWC, should not be in the list to start with, since they already have a way to enabled/disable their presence (tile services show up a "gwc" in the service security configuration, in other words, GeoServer sees any tile service as "gwc").

Current services perform that kind of selection by means of accessing the catalog and looking for specific type of resources, hence this knowledge is not generally available. Also, services are pluggable and it's not possible predict what service makes sense for future services. As a result, an extension point is going to be added that will vote on the suitability of a service for a given layer:

/**
 * Allows to verify is a given layer is suitable for publishing on a given service. A single negative vote will 
 * make the service disappear from the selective service layer UI 
 */
interface ServiceResourceVoter {

   /**
    * Returns true if the services is not considered suitable for the given layer. In case the answer 
    * is unknown by this voter, false will be returned
    */
   boolean hideService(String service, ResourceInfo resource);
}

The interface will be added in gs-main, one of the above filters will be registered in the application context in each service module that need selective resource behavior (WFS, WCS, GWC).

In order to limit availability of layers to services a CatalogFilter will be implemented, mimicking the behavior of the existing DisabledResourcefilter, that is:

    Verify if the current request is a OGC one, and what service is being used
    Verify if the layer has selective service configuration
    Hide the layer if the service in question is in the list of the disabled services (case insensitive)

REST API wise, the new attributes are going to show up in the resource description endpoint, the changes will make sure the new attributes show up properly in the XML/JSON outputs.

Finally, we are going to add a new setting (system/env/servlet context variable) named org.geoserver.service.disabled which accepts a comma separated list of services that should be disabled by default, in case the resource in question has no explicit configuration.
Backwards Compatibility

There are two backwards compatibility scenarios that need to be considered:

    Users upgrading the data directory from a version that did not have selective service configurations
    Users plugging-in a new service while selective service configurations are already in place

The first set of users, upgrading GeoServer from an older version, will miss the serviceConfiguration flag, which defaults to false, preserving operation of all services.

The second set of users, adding a new service while having the selective configuration enabled, won't have the service name in the disabledServices list, hence enabling the service by default on all layers (this default is debatable, there is not "right" solution, but adding a service that cannot be used out of the box because layers do not list it seems problematic, if the issue is security related users can switch to use a proper security system instead).

Since adding a new service is a matter of installing extensions and restarting the container, the admin is in a position to also alter the configuration accordingly, which can be done using the UI, if there are few layers, or via the REST API, if automation is required.
Feedback
Voting

Project Steering Committee:

    Alessio Fabiani:
    Andrea Aime: +1
    Brad Hards: +1
    Ian Turton: +1
    Jody Garnett: +1
    Jukka Rahkonen: +1
    Kevin Smith:
    Simone Giannecchini: +1

Links

No links available for the time being
