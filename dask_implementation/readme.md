# Dask Implementation
## Outcomes
Able to parallel processes large ODC datasets to get results to users where memory limits would normally be reached and no results generated.
## Description
The Jupyter sandbox environments are great for sharing code examples and running queries on subsets of the available data.
Users can however run into trouble running queries on larger datasets due to memory limits in place to manage the cost of the environment.

To find a cost effective and sustainable solution to this problem we want to implement a distributed cluster to parallel process larger datasets. Dask is popular open source tool we can use for this and only need to adjust our existing python workflows to utilise the Dask Cluster.
 
Tasks:
- Create a Dask Cluster with workers that can process ODC data
- Connect that cluster up to the sandbox environments
- Test users can submit queries to the cluster
