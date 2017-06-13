var todoApp = angular.module('todoApp',['ngRoute'], function($interpolateProvider){
	$interpolateProvider.startSymbol('[[');
	$interpolateProvider.endSymbol(']]');
})

todoApp.controller("IndexController",['$scope', '$http','$route','$window',function($scope,$http,$route,$window){
	if ($window.user != null) {
		$scope.username = $window.user.name;
		$scope.todo_form = ""
		
		$http({
			url:'/get_tasks',
			method:'GET'
		})
		.then(function onSuccess(response){
			$scope.tasks = response.data.tasks
		})

		$scope.addTask = function(todo_form){
			$http({
				url:'/tasks/add_task',
				method:'POST',
				data:JSON.stringify({'form':todo_form}),
				headers:{'Content-Type':'application/json'}
			})
			.then(function onSuccess(response){
				$scope.tasks = response.data.tasks
				$scope.todo_form = []
			}, function onError(response){
				console.response
				swal('Oops!',response.data.message,'error').catch(swal.noop)
			})
		}

		$scope.popEdit = function(task){
			$scope.update_todo_form = angular.copy(task)
			$('#edit-todo-modal').modal('show');
		}
		$scope.editTask = function(task){
			$http({
				url:'/tasks/edit_task',
				method:'POST',
				data:JSON.stringify({'task':task}),
				headers:{'Content-Type':'application/json'}
			})
			.then(function onSuccess(response){
				$scope.tasks = response.data.tasks
			}, function onError(response){
				swal('Oops!',response.data.message,'error').catch(swal.noop)
			})
		}
		$scope.removeTask = function(task){
			$http({
				url:'/tasks/remove_task',
				method:'POST',
				data:JSON.stringify({'task':task.id}),
				headers:{'Content-Type':'application/json'}
			})
			.then(function onSuccess(response){
				$scope.tasks = response.data.tasks
			}, function onError(response){
				swal('Oops!',response.data.message,'error').catch(swal.noop)
			})
		}

	} 
}]);

todoApp.controller("LoginController",['$scope', '$http','$route','$window',function($scope,$http,$route,$window){
	$scope.login_form = "";

	$scope.login = function(){
		$http({
			url:'/login',
			method:'POST',
			data:JSON.stringify({'form':$scope.login_form}),
			headers:{'Content-Type':'application/json'}
		})
		.then( function onSuccess(response){
			if (response.data.status == true) {
				$window.location = '/'
			}
			else{
				swal('Login failed!',response.data.message,'error').catch(swal.noop);
			}
		})
	}
}]);

todoApp.controller("SignupController",['$scope', '$http','$route',function($scope,$http,$route){

	$scope.signup_form = "";

	$scope.cnfpassword = function(){
		if ($scope.signup_form.cnfpassword == $scope.signup_form.password)
			$scope.signup_form.cnfClass = "has-success";
		else
			$scope.signup_form.cnfClass = "has-error";
	}
	$scope.signup = function(){
		console.log($scope.signup_form)
		$http({
			url:'/signup',
			method:'POST',
			data:JSON.stringify({'form':$scope.signup_form}),
			headers:{'Content-Type':'application/json'}
		})
		.then(function onSuccess(response){
			$scope.message = response.data.message;
			console.log($scope.docs);
		}).catch(swal.noop)
	}
}]);

todoApp.controller("LogoutController",['$scope', '$http','$route','$window',function($scope,$http,$route,$window){
	$http({
		url:'/logout',
		method:'GET'
	})
	.then(function onSuccess(response){
		if (response.data.status == true) {
			swal({
					title: 'You have been logged out!',
					text: response.data.message,
					type:'success',
					timer: 1000
					})
				.then(
					function () {},
					// handling the promise rejection
					function (dismiss) {
					if (dismiss === 'timer') {
						$window.location = '/'
					}
				})
		}

		$scope.message = response.data.message;
		console.log($scope.message);
	})
}]);

todoApp.config(function($routeProvider){
	$routeProvider.when('/',{
		controller:'IndexController',templateUrl:'../static/pages/home.html'
	}).when('/login',{
		controller:'LoginController',templateUrl:'../static/pages/login.html'
	}).when('/signup',{
		controller:'SignupController',templateUrl:'../static/pages/signup.html'
	}).when('/logout',{
		controller:'LogoutController',templateUrl:'../static/pages/home.html'
	})
})