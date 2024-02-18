module.exports = {
   getUser: function() {
      const user = sessionStorage.getItem('user');
      if(user ==='undefined' || !user) {
         return null;
      }else {
         return JSON.parse(user);
      }
   },

   getToken: function() {
      return sessionStorage.getItem('token');
   },

   setUserSession: function(user, token, launchGPU) {
      sessionStorage.setItem('user', JSON.stringify(user));
      sessionStorage.setItem('token', token);
      sessionStorage.setItem('launchGPU', launchGPU);
   },
   resetUserSession: function() {
      sessionStorage.removeItem('user');
      sessionStorage.removeItem('token');
      sessionStorage.removeItem('launchGPU');
   }
}