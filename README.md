# From scratch to DNS exfiltration detection with logs 
## Création du cluster
`$kind create cluster --config=kind-config.yaml

## Installation de Cilium CLI
https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/#install-the-cilium-cli

## Installation de Cilium avec Helm 
`$helm repo add cilium https://helm.cilium.io/
`$helm install cilium cilium/cilium --namespace kube-system`


Puis vérification : 
`$helm list -n kube-system`
`$cilium status
Et teste de connectivité : `$cilium connectivity test
(Ce test prend du temps)

Si le test échoue lors du déploiement des pods, augmenter les limites des ressources inotify : 
- `$sudo sysctl fs.inotify.max_user_instances=512
- `$sudo sysctl fs.inotify.max_user_watches=524288

## Installer Hubble CLI
https://docs.cilium.io/en/stable/gettingstarted/hubble_setup/#install-the-hubble-client

## Installer Hubble avec helm
Pour pouvoir exporter les network flow logs, il faut installer la version >=1.16.0 de cilium 

Attention ! Pour pouvoir utiliser l'exportation des logs, il faut upgrade cilium en une version plus récente cilium ([lien pour plus d'infos](https://docs.cilium.io/en/latest/observability/hubble-exporter/)): 
```
$curl -LO https://github.com/cilium/cilium/archive/main.tar.gz
$tar xzf main.tar.gz
$cd cilium-main/install/kubernetes
$helm upgrade cilium ./cilium --namespace kube-system --set hubble.enabled=true --set hubble.export.static.enabled=true --set hubble.export.static.filePath=/var/run/cilium/hubble/events.log
```
Puis on déploie Hubble Relay et Hubble UI : 
```
$helm upgrade cilium cilium/cilium ./cilium --namespace kube-system --reuse-values --set hubble.relay.enabled=true --set hubble.ui.enabled=true`
```
## Vérifier Hubble et Hubble UI 
`$cilium status`

Pour rappel : 
![[Pasted image 20240528184446.png]]
Pour rendre accessible Hubble Relay : `$cilium hubble port-forward` (dans une autre console, idéalement tmux)

Ensuite, pour vérifier l'état d'Hubble avec Hubble CLI : `$hubble status`

Pour utiliser hubble ui : `$cilium hubble ui 
Pour hubble ui, besoin d'un browser, donc potentiellement d'un proxy
Par exemple : `$caddy reverse-proxy --from :8080 --to localhost:12000`

![[Pasted image 20240623010956.png]]

## Permettre de la visibilité L7
Enfin, on ajoute une règle DNS pour permettre la visibilité (https://docs.cilium.io/en/stable/observability/visibility/#proxy-visibility)
`$kubectl apply -f shallow-rule.yaml`

## Générer du traffic:
```
$kubectl apply -f python-exfiltration/python-pod.yaml
$kubect exec -it python-script-runner -- bin/bash
$python3 dns_exfiltration_official.py
```

## Visualiser les logs avec Hubble CLI
`$hubble observe --protocol dns`

## Vérifier que les logs sont exportés
`$kubectl exec -n kube-system $CILIUM_POD -- cat /var/run/cilium/hubble/events.log | grep dns | tail 5`

## Récupérer les logs 
```
$cd PRIM_Cilium/log-processing
$./fetch.sh
```
## Détection des exfiltrations DNS

Librairies python requises:
- pandas
- numpy
- tensorflow

`$python3 classify-dns.py`

## Generate customized traffic
```
$kubectl apply -f ubuntu-pod/ubuntu-pod.yaml
$kubectl exec -it ubuntu-network-tools-pod -- /bin/bash
```
Then you can "dig" the queries you want 
For automatic DNS exfiltration tools, see "generate traffic", there are 3 python scripts to do so



# From scratch to DNS exfiltration detection with dashboards
## Création du cluster
`$kind create cluster --config=kind-config.yaml

## Installation de Cilium CLI
https://docs.cilium.io/en/stable/gettingstarted/k8s-install-default/#install-the-cilium-cli

## Installation de Cilium avec Helm 
`$helm repo add cilium https://helm.cilium.io/
`$helm install cilium cilium/cilium --namespace kube-system`


Puis vérification : 
`$helm list -n kube-system`
`$cilium status
Et teste de connectivité : `$cilium connectivity test
(Ce test prend du temps)

Si le test échoue lors du déploiement des pods, augmenter les limites des ressources inotify : 
- `$sudo sysctl fs.inotify.max_user_instances=512
- `$sudo sysctl fs.inotify.max_user_watches=524288


## Installer Hubble avec helm
Pour installer Hubble, il suffit de modifier les values de cilium dans Helm. Ensuite, pour configurer Hubble, cela se passe encore par ces values
Pour une raison qui m'échappe, le pod Hubble-relay ne fonctionne pas ("can't find peers") dans certains cas
Bug de Hubble relay ? [[Hubble relay can't find peers]]
Pour le faire fonctionner : 
```
$helm install cilium cilium/cilium --version 1.15.6 \
  --namespace kube-system \
  --set prometheus.enabled=true \
  --set operator.prometheus.enabled=true \
  --set hubble.enabled=true \
  --set hubble.metrics.enableOpenMetrics=true \
  --set hubble.metrics.enabled="{dns:query,drop,tcp,flow,port-distribution,icmp,httpV2:exemplars=true;labelsContext=source_ip\,source_namespace\,source_workload\,destination_ip\,destination_namespace\,destination_workload\,traffic_direction}"
$helm upgrade cilium cilium/cilium --version 1.15.6 \
   --namespace kube-system \
   --reuse-values \
   --set hubble.relay.enabled=true \
   --set hubble.ui.enabled=true
```
## Installer Hubble UI
https://docs.cilium.io/en/stable/gettingstarted/hubble_setup/#install-the-hubble-client

## Vérification de l'état d'Hubble
`$cilium status`

Pour rappel : 
![[Pasted image 20240528184446.png]]
Pour rendre accessible Hubble Relay : `$cilium hubble port-forward` (dans une autre console, idéalement tmux)

Ensuite, pour vérifier l'état d'Hubble avec Hubble CLI : `$hubble status`

Pour utiliser hubble ui : `$cilium hubble ui 
Pour hubble ui, besoin d'un browser, donc potentiellement d'un proxy
Par exemple : `$caddy reverse-proxy --from :8080 --to localhost:12000`

![[Pasted image 20240623010956.png]]

## Installer Grafana et Prometheus
```bash
$helm repo add grafana https://grafana.github.io/helm-charts
$helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$helm install grafana grafana/grafana --namespace monitoring --create-namespace
$helm install prometheus prometheus-community/prometheus --namespace monitoring
```
## Exposer grafana
`$kubectl port-forward -n monitoring $GRAFANA_POD_NAME 3000`
Puis reverse proxy caddy si besoin 

Suivre les instructions données lors de l'installation de Grafana pour les identifiants 

## Exposer prometheus
`$kubectl port-forward -n monitoring $PROMETHEUS_SERVER_POD_NAME 9090`

## Permettre de la visibilité L7
Enfin, on ajoute une règle DNS pour permettre la visibilité (https://docs.cilium.io/en/stable/observability/visibility/#proxy-visibility)
`$kubectl apply -f shallow-rule.yaml`

## Générer du traffic:
```
$kubectl apply -f python-exfiltration/python-pod.yaml
$kubect exec -it python-script-runner -- bin/bash
$python3 dns_exfiltration_official.py
```

Attention : pour que les metrics fonctionnent (customisation des labels), il faut avoir une version de Cilium >1.15.0

(On obtient bien les metrics, mais pas les bons labels...pb de version ? Encore ?)

## Modifier les metrics
https://docs.cilium.io/en/stable/observability/metrics/
- Modifier le fichier values.yaml qu'utilise Helm
- Appliquer ces changements : `helm upgrade cilium cilium/cilium --namespace kube-system --values Cilium/cilium-values.yaml `
- Relancer Hubble : `kubectl rollout restart deployment hubble-relay -n kube-system`
- Simuler traffic
- Fetch sur les metrics sur prometheus. Eventuellement relancer le port forward 
  ![[Pasted image 20240529213714.png]]
- Si jamais prometheus n'affiche rien, aller chercher les metrics directement depuis le endpoint, cad le port 9965 du noeud identifié

## Générer des dashboards 
Des exemples de dashboards pertinents pour les détecter des exfiltration DNS haut débit sont dans le dossier grafana-dashboards
