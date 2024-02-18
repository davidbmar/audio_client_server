import React, { useState }  from 'react';
const terminatePod = async (podId, onRefresh) => {
   try {
      const response = await fetch('https://fmi6vgzxb1.execute-api.us-east-2.amazonaws.com/staging/terminatePod', {
         method: 'DELETE',
         headers: {
           'x-api-key': '7cEGIf76VI31qPawLnbjJ3ix6LGuS8BJ51AleTwm',
           'Content-Type': 'application/json', // Specify the content type
         },
         body: JSON.stringify({ pod_id: podId }), // Include pod_id in the request body
      });
      if (response.ok) {
         const data = await response.json();
         console.log('TERMINATED POD:', data);
         // After stopping the pod, wait for 3 seconds and refresh the pods list
         onRefresh(); // This will be called immediately after stopPod; the delay is handled in onRefresh to update the list of pods.
      } else {
         // Handle HTTP errors
         console.error('HTTP error', response.status, await response.text());
      }
   } catch (error) {
      console.error('Fetch error:', error);
   }
};
const stopPod = async (podId, onRefresh) => {
   try {
      const response = await fetch('https://fmi6vgzxb1.execute-api.us-east-2.amazonaws.com/staging/stopPod', {
         method: 'POST',
         headers: {
           'x-api-key': '7cEGIf76VI31qPawLnbjJ3ix6LGuS8BJ51AleTwm',
           'Content-Type': 'application/json', // Specify the content type
         },
         body: JSON.stringify({ pod_id: podId }), // Include pod_id in the request body
      });
      if (response.ok) {
         const data = await response.json();
         console.log('STOPPED POD:', data);
         // After stopping the pod, wait for 3 seconds and refresh the pods list
         onRefresh(); // This will be called immediately after stopPod; the delay is handled in onRefresh to update the list of pods.
      } else {
         // Handle HTTP errors
         console.error('HTTP error', response.status, await response.text());
      }
   } catch (error) {
      console.error('Fetch error:', error);
   }
};
 
const PodsTable = ({ pods, onRefresh }) => {
   const [selectedPods, setSelectedPods] = useState({});

   const getSelectedPodIds = () => {
      return Object.entries(selectedPods).filter(([_, isSelected]) => isSelected).map(([id, _]) => id);
   };

   const togglePodSelection = (id) => {
      setSelectedPods(prev => ({
        ...prev,
        [id]: !prev[id]
      }));
   };

   const handleSelectAll = (e) => {
      const newSelectedPods = {};
      pods.forEach(pod => {
         newSelectedPods[pod.id] = e.target.checked;
      });
      setSelectedPods(newSelectedPods);
   };

   return (
      <table>
         <thead>
            <tr>
               <th><input type="checkbox" onChange={handleSelectAll} /></th>
               <th>ID</th>
               <th>Name</th>
               <th>Status</th>
               <th>Last Status Change</th>
            </tr>
         </thead>
         <tbody>
            {pods.map(pod => (
               <tr key={pod.id}>
                 <td><input type="checkbox" checked={!!selectedPods[pod.id]} onChange={() => togglePodSelection(pod.id)} /></td>
                 <td>{pod.id}</td>
                 <td>{pod.name}</td>
                 <td>{pod.desiredStatus}</td>
                 <td>{pod.lastStatusChange}</td>
                 <td><button onClick={() => stopPod(pod.id, onRefresh)}>Stop</button></td>
                 <td><button onClick={() => terminatePod(pod.id, onRefresh)}>Terminate</button></td>
               </tr>
            ))}
         </tbody>
      </table>
    );

};

export default PodsTable;
