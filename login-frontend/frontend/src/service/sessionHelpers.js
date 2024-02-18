// ./service/sessionHelpers.js
export function getLaunchGPUStatus() {
   return sessionStorage.getItem('launchGPU') === 'true'; // Convert string to boolean
}